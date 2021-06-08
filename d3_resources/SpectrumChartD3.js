/* 
This is part of Cambio 2.1 program (https://hekili.ca.sandia.gov/cambio) and is licensed under the LGPL v2.1 license
   
   This library is free software; you can redistribute it and/or
   modify it under the terms of the GNU Lesser General Public
   License as published by the Free Software Foundation; either
   version 2.1 of the License, or (at your option) any later version.

   This library is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   Lesser General Public License for more details.

   You should have received a copy of the GNU Lesser General Public
   License along with this library; if not, write to the Free Software
   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

   
Feature TODO list (created 20160220):
  - For the y-axis scalers, should add some padding on either side of that area
    and also make the width of each slider more than 20px if a touch device and
    also increase radius of sliderToggle.
    - The number given at bottom of scaler while adjusting is cut off on the right side
  - Need some way to filter reference gamma lines to not draw insignificant lines.  Ex, Th232 gives ~900 dom elements, which can slow things down
  - When changing x-range with x-axis slider chart, it constantly calls back to C++ - this should be changed so it only happens when you you stop adjusting this
    - Could make it so its emmitted only when self.sliderBoxDown changes from true to false, and similar for touch and edges of box
  - Fix intermitten issue of zooming in messes up (especially aver dragging starting from the y-axis title)
    - (was this maybe fixed by ensuring getting animation frames is terminated?)
  - Make it so x-axis binning is given seperately for each histogram
  - Add statistical error bars
  - Add support for deviation pairs with polynomial energy calibration (instead of just lower edge energy)
  - Customize mouse point to zoom-in/zoom-out where appropriate
  - Optimize frequency of rebinning of data (prevent extra rebinned data from being drawn)
  - Move to using D3 v5 with modules to minimize code sizes and such.
  - Start compiling with babel to take care of all the poly fills.
  - For peak labels, make a border around text (maybe add some padding, maybe make border same color as peak), make background translucent so you can read the text even if in a cluttered area.
  - Make sure that d3 selections are iterated over using each(...), rather than forEach(...)
  - lots of other issues
*/

SpectrumChartD3 = function(elem, options) {
  var self = this;

  // Add any polyfills needed to run D3 code
  browserPolyfill();

  this.chart = typeof elem === 'string' ? document.getElementById(elem) : elem; 

  this.cx = this.chart.clientWidth;
  this.cy = this.chart.clientHeight;

  this.options = options || {}; 
  
  //if( (typeof this.options.yscale) !== 'string' || (['lin', 'log', 'sqrt'].indexOf(this.options.yscale) < 0) ) this.options.yscale = "lin";
  if( (typeof this.options.yscale) !== 'string' ) this.options.yscale = "lin";
  if( (typeof this.options.gridx) !== 'boolean' ) this.options.gridx = false;
  if( (typeof this.options.gridy) !== 'boolean' ) this.options.gridy = false;
  if( (typeof this.options.compactXAxis) !== 'boolean' ) this.options.compactXAxis = false;
  if( (typeof this.options.adjustYAxisPadding) !== 'boolean' ) this.options.adjustYAxisPadding = true;
  if( (typeof this.options.wheelScrollYAxis) !== 'boolean' ) this.options.wheelScrollYAxis = true;
  
  //if( (typeof this.options.) !== '' ) this.options. = ;
  
  if(typeof options.animationDuration !== 'number' || options.animationDuration < 0) this.options.animationDuration = 1000;
  this.options.showAnimation = (typeof options.showAnimation == 'boolean' && this.options.animationDuration > 0) ? options.showAnimation : false;
  if( (typeof this.options.showXAxisSliderChart) !== 'boolean' ) this.options.showXAxisSliderChart = false;
  
  if( (typeof options.sliderChartHeightFraction !== 'number') || options.sliderChartHeightFraction <= 0 || options.sliderChartHeightFraction > 0.75 )
    this.options.sliderChartHeightFraction = 0.1;

  this.options.allowPeakFit = /*(typeof options.allowPeakFit == 'boolean') ? options.allowPeakFit :*/ false;

  this.options.showUserLabels = (typeof options.showUserLabels == 'boolean') ? options.showUserLabels : false;
  this.options.showPeakLabels = (typeof options.showPeakLabels == 'boolean') ? options.showPeakLabels : false;
  this.options.showNuclideNames = (typeof options.showNuclideNames == 'boolean') ? options.showNuclideNames : false;
  this.options.showNuclideEnergies = (typeof options.showNuclideEnergies == 'boolean') ? options.showNuclideEnergies : false;
  
  if( (typeof this.options.showLegend) !== 'boolean' ) this.options.showLegend = true;
  if( (typeof this.options.scaleBackgroundSecondary) !== 'boolean' ) this.options.scaleBackgroundSecondary = false;


  this.options.refLineTopPad = 30;
  
  self.options.logYFracTop = 0.05;
  self.options.logYFracBottom = 0.025;
  self.options.linYFracTop = 0.1;
  self.options.linYFracBottom = 0.1;
  self.options.sqrtYFracTop = 0.1;
  self.options.sqrtYFracBottom = 0.1;

  this.options.showRefLineInfoForMouseOver = (typeof options.showRefLineInfoForMouseOver == 'boolean') ? options.showRefLineInfoForMouseOver : true;
  this.options.showMouseStats = (typeof options.showMouseStats == 'boolean') ? options.showMouseStats : true;
  this.options.showComptonEdge = (typeof options.showComptonEdge == 'boolean') ? options.showComptonEdge : false;
  this.options.showComptonPeaks = (typeof options.showComptonPeaks == 'boolean') ? options.showComptonPeaks : false;
  this.options.comptonPeakAngle = (typeof options.comptonPeakAngle == 'number' && !isNaN(options.comptonPeakAngle)) ? options.comptonPeakAngle : 180;
  this.options.showEscapePeaks = (typeof options.showEscapePeaks == 'boolean') ? options.showEscapePeaks : false;
  this.options.showSumPeaks = (typeof options.showSumPeaks == 'boolean') ? options.showSumPeaks : false;
  this.options.backgroundSubtract = (typeof options.backgroundSubtract == 'boolean') ? options.backgroundSubtract : false;
  this.options.allowDragRoiExtent = (typeof options.allowDragRoiExtent == 'boolean') ? options.allowDragRoiExtent : true;
  
  
  self.options.spectrumLineWidth = (typeof options.spectrumLineWidth == 'number' && options.spectrumLineWidth>0 && options.spectrumLineWidth < 15) ? options.spectrumLineWidth : 1.0;
  
  // Set which spectrums to draw peaks for
  this.options.drawPeaksFor = {
    FOREGROUND: true,
    BACKGROUND: true,
    SECONDARY: false,
  };

  this.options.showXRangeArrows = (typeof options.showXRangeArrows == 'boolean') ? options.showXRangeArrows : true;

  this.options.maxScaleFactor = 10;

  this.padding = {
     "top":  5,
     "titlePad" : 5,
     "right":   10,
     "bottom": 5,
     "xTitlePad": 5,
     "left":     5,
     "labelPad": 5,
     "title":    23,
     "label":    8,
     "sliderChart":    8,
  };
  
  this.padding.leftComputed = this.padding.left + this.padding.title + this.padding.label + this.padding.labelPad;
  this.padding.topComputed = this.padding.top + this.padding.titlePad + 15;
  this.padding.bottomComputed = this.padding.bottom +  this.padding.xTitlePad + 15;
  
  this.size = {
    "width":  Math.max(0, this.cx - this.padding.leftComputed - this.padding.right),
    "height": Math.max(0, this.cy - this.padding.topComputed  - this.padding.bottomComputed),
    "sliderChartHeight": 0,
    "sliderChartWidth": 0,
  };

  /**
   * Added by Christian 20180215
   * Used to differentiate between different types of spectra, and for future additional usage
   * Each spectrum object should have an associated type with it, which we can compare using this enum.
   */
  this.spectrumTypes = {
    FOREGROUND: 'FOREGROUND',
    BACKGROUND: 'BACKGROUND',
    SECONDARY: 'SECONDARY',
  };

  /*pre IE9 support */
  if (!Array.isArray) {
    Array.isArray = function(arg) {
      return Object.prototype.toString.call(arg) === '[object Array]';
    };
  }

  /*When dragging the plot, both dragging_plot and zooming_plot will be */
  /*  true.  When only zooming (e.g. mouse wheel), then only zooming_plot */
  /*  will be true. */
  this.dragging_plot = false;
  this.zooming_plot = false;

  this.refLines = [];

  /* x-scale */
  this.xScale = d3.scale.linear()
      .domain(this.options.xScaleDomain ? this.options.xScaleDomain : [0, 3000])
      .range([0, this.size.width]);

  /* drag x-axis logic */
  this.xaxisdown = null;

  if( this.options.yscale === "log" ) {
    this.yScale = d3.scale.log().clamp(true).domain([0, 100]).nice().range([1, this.size.height]).nice();
  } else if( this.options.yscale === "sqrt" ) {
    this.yScale = d3.scale.pow().exponent(0.5).domain([0, 100]).range([0, this.size.height]);
  } else {
    this.yScale = d3.scale.linear().domain([0, 100]).nice().range([0, this.size.height]).nice();
  }
  
  if( this.yGrid )
    this.yGrid.scale( this.yScale );
      
  this.yaxisdown = Math.NaN;

  /* Finds distance between two points */
  this.dist = function (a, b) {
    return Math.sqrt(Math.pow(a[0]-b[0],2) + Math.pow(a[1]-b[1],2));
  };

  this.min_max_x_values = function() {
    if (!self.rawData || !self.rawData.spectra || !self.rawData.spectra.length)
      return [-1,-1];

    var min = null, max = null;
    self.rawData.spectra.forEach(function(spectrum) {
      if (!spectrum.x)
        return;

      if (min == null || spectrum.x[0] < min) min = spectrum.x[0];
      if (max == null || spectrum.x[spectrum.x.length-1] > max) max = spectrum.x[spectrum.x.length-1];
    });

    return [min,max];
  };

  this.displayed_raw_start = function(spectrum){
    if( !self.rawData || !self.rawData.spectra || !self.rawData.spectra.length )
      return -1;
    var xstart = self.xScale.domain()[0];
    if (!spectrum)
      spectrum = self.rawData.spectra[0]; /* use foreground by default */

 /* switch to using: */
 /* var bisector = d3.bisector(function(d){return d.x;}); */
 /* bisector.left(spectrum.x, xstart) */

    var i = 0;
    while( i < spectrum.x.length && spectrum.x[i] < xstart )
      ++i;
    return i;
  };

  this.displayed_raw_end = function(spectrum){
    if( !self.rawData || !self.rawData.spectra || !self.rawData.spectra.length)
      return -1;
    var xend = self.xScale.domain()[1];
    if (!spectrum)
      spectrum = self.rawData.spectra[0]; /* use foreground by default */
    var i = spectrum.x.length - 1;
    while( i > 0 && spectrum.x[i] > xend )
      --i;
    return i + 1;
  };

  this.displayed_start = function(spectrum){
    if( !spectrum || !spectrum.points || !spectrum.points.length )
      return -1;
    var xstart = self.xScale.domain()[0];
    var i = 0;
    while( i < spectrum.points.length && spectrum.points[i].x <= xstart )
      ++i;
    return Math.max(i - 1,0);
  };

  this.displayed_end = function(spectrum){
    if( !spectrum || !spectrum.points || !spectrum.points.length )
      return -1;
    var xend = self.xScale.domain()[1];
    var i = spectrum.points.length - 1;
    while( i > 0 && spectrum.points[i].x >= xend )
      --i;
    return Math.min(i + 1, spectrum.points.length);
  };

  this.firstRaw = this.lastRaw = this.rebinFactor = -1;

  this.do_rebin();

  this.setYAxisDomain = function(){
    if( !isNaN(self.yaxisdown) )
      return;
    var yaxisDomain = self.getYAxisDomain(),
        y1 = yaxisDomain[0],
        y0 = yaxisDomain[1];
    this.yScale.domain([y1, y0]);
  }
  this.setYAxisDomain();


  /* drag y-axis logic */
  this.yaxisdown = Math.NaN;

  this.dragged = this.selected = null;


  this.vis = d3.select(this.chart).append("svg")
      .attr("width",  this.cx)
      .attr("height", this.cy)
      .append("g")
      .attr("transform", "translate(" + this.padding.leftComputed + "," + this.padding.topComputed + ")");

  this.plot = this.vis.append("rect")
      .attr("width", this.size.width)
      .attr("height", this.size.height)
      .attr("id", "chartarea"+this.chart.id )
      .attr("class", "chartarea" )
      //.style("fill", "#EEEEEE")
      ;
      /*.attr("pointer-events", "all"); */

  this.svg = d3.select(self.chart).select('svg');

  /*
  Chart vs. Vis vs. Document Body
  ___________________________________________
  | _______________________________________ |
  ||  ___________________________________  ||
  || |                                   | ||
  || |           VIS (SPECTRUM)          | ||
  || |                                   | ||
  || |___________________________________| ||
  ||                                       ||
  ||                  CHART                ||
  ||_______________________________________||
  |                                         |
  |                                         |
  |                   BODY                  |
  |                                         |
  |                                         |
  |_________________________________________|
  */

  /* 
  NOTE: Restoring the zoom behavior only for touch events
        This does NOT affect the behavior for other mouse events.
        Restoring the zoom behavior allows pinch zooming/panning with touch interactions.
  */
  this.zoom = d3.behavior.zoom()
    .x(self.xScale)
    .y(self.yScale)
    .on("zoom", self.handleZoom())
    .on("zoomend", self.handleZoomEnd());

  /* Vis interactions */
  this.vis
    .call(this.zoom)
    //.on("click", function(){ console.log( 'Single CLick!' ); } )
    //.on("dblclick", function(){ console.log( 'DOuble CLick!' ); } )  //ToDo: Use 'dblclick' signal rahter than custom one
    .on("mousedown", self.handleVisMouseDown())
    .on("mouseup", self.handleVisMouseUp())
    .on("wheel", self.handleVisWheel())
    .on("touchstart", self.handleVisTouchStart())
    .on("touchmove", self.handleVisTouchMove())
    .on("touchend", self.handleVisTouchEnd());

  /* Cancel the zooms for mouse events, we'll use our own implementation for these (however, keeping the touch zooming) */
  this.vis
    .on("mousedown.zoom", null)
    .on("mousemove.zoom", null)
    .on("mouseup.zoom", null)
    .on("mouseover.zoom", null)
    .on("mouseout.zoom", null)
    .on("wheel.zoom", null)
    .on("click.zoom", null)
    .on("dblclick.zoom", null);

  /// @TODO triggering the cancel events on document.body and window is probably a bit agressive; could probably do this for just this.vis + on leave events
  d3.select(document.body)
    .on("mouseup", self.handleCancelAllMouseEvents() )
  d3.select(window)
    .on("mouseup", self.handleCancelAllMouseEvents())
    .on("mousemove", function() {
        if( d3.event && (self.sliderBoxDown || self.leftDragRegionDown || self.rightDragRegionDown || self.currentlyAdjustingSpectrumScale) ) {
          d3.event.preventDefault();
          d3.event.stopPropagation();
        }
      });



  /*  Chart Interactions */
  d3.select(this.chart)
    .on("mousemove", self.handleChartMouseMove())
    .on("mouseleave", self.handleChartMouseLeave())
    .on("mouseup", self.handleChartMouseUp())
    .on("wheel", self.handleChartWheel())
    .on("touchstart", self.handleChartTouchStart())
    .on("touchend", self.handleChartTouchEnd());

  /*
  To allow markers to be updated while mouse is outside of the chart, but still inside the visual.
  */
  this.yAxis = d3.svg.axis().scale(this.yScale)
   .orient("left")
   .innerTickSize(7)
   .outerTickSize(1)
   .ticks(0);

  this.yAxisBody = this.vis.append("g")
    .attr("class", "yaxis" )
    .attr("transform", "translate(0,0)")
    .call(this.yAxis);

  this.xAxis = d3.svg.axis().scale(this.xScale)
   .orient("bottom")
   .innerTickSize(7)
   .outerTickSize(1)
   .ticks(20, "f");

  this.xAxisBody = this.vis.append("g")
    .attr("class", "xaxis" )
    .attr("transform", "translate(0," + this.size.height + ")")
    .style("cursor", "ew-resize")
    //.on("mouseover", function(d, i) { /*d3.select(this).style("font-weight", "bold");*/})
    //.on("mouseout",  function(d) { /*d3.select(this).style("font-weight", null);*/ })
    .on("mousedown.drag",  self.xaxisDrag())
    .on("touchstart.drag", self.xaxisDrag())
    .call(this.xAxis)
    ;

  this.vis.append("svg:clipPath")
    .attr("id", "clip" + this.chart.id )
    .append("svg:rect")
    .attr("x", 0)
    .attr("y", 0)
    .attr("width", this.size.width )
    .attr("height", this.size.height );

  self.addMouseInfoBox();

  /*Make a <g> element to draw everything we want that follows the mouse around */
  /*  when we're displaying reference photopeaks.  If the mouse isnt close enough */
  /*  to a reference line, then this whole <g> will be hidden */
  self.refLineInfo = this.vis.append("g")
    .attr("class", "refLineInfo")
    .style("display", "none");

  /*Put the reference photopeak line text in its own <g> element so */
  /*  we can call getBBox() on it to get its extent to to decide where to */
  /*  position the text relative to the selected phtotopeak. */
  self.refLineInfoTxt = self.refLineInfo.append("g");

  /*Add the text to the <g>.  We will use tspan's to append each line of information */
  self.refLineInfoTxt.append("text")
   .attr("x", 0)
   .attr("dy", "1em");

  /*Add a small red circle on the x axis to help indicate which line the info is */
  /*  currently showing for. */
  self.refLineInfo.append("circle")
    .attr("cx", 0)
    .attr("cy", self.size.height)
    .attr("r", 2)
    .style("fill","red");

  this.chartBody = this.vis.append("g")
    .attr("clip-path", "url(#clip" + this.chart.id + ")");

  self.peakVis = this.vis.append("g")
    .attr("class", "peakVis")
    .attr("transform","translate(0,0)")
    .attr("clip-path", "url(#clip" + this.chart.id + ")");

  /* add Chart Title */
  var title = this.options.title;
  this.options.title = null;
  this.setTitle( title, true );

  /* Add the x-axis label */
  if (this.options.xlabel) {
    this.xaxistitle = this.svg.append("text")
        .attr("class", "xaxistitle")
        .text(this.options.xlabel)
        .attr("x", this.size.width/2)
        .attr("y", this.size.height )
        .attr("dy",29)
        .style("text-anchor","middle");
  }

  /* add y-axis label */
  if (this.options.ylabel) {
    this.vis.append("g")
      .attr('id', 'yaxistitle-container') // Christian: To allow changing the y-axis title
      .append("text")
        .attr("class", "yaxistitle")
        .text(this.options.ylabel + (this.rebinFactor > 1 ? (" per " + this.rebinFactor + " Channels") : "") )
        .style("text-anchor","middle");
        /*.attr("transform","translate(" + -40 + " " + this.size.height/2+") rotate(-90)"); */
  }
}

registerKeyboardHandler = function(callback) {
  var callback = callback;
  d3.select(window).on("keydown", callback);
}

/**
 * Adds polyfills needed to run D3 code on older browsers such as IE11.
 */
browserPolyfill = function() {

  // Thanks to: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/assign
  //  Christian: Added to support Object.assign(...) method for IE11
  if (typeof Object.assign != 'function') {
    // Must be writable: true, enumerable: false, configurable: true
    Object.defineProperty(Object, "assign", {
      value: function assign(target, varArgs) { // .length of function is 2
        'use strict';
        if (target == null) { // TypeError if undefined or null
          throw new TypeError('Cannot convert undefined or null to object');
        }
  
        var to = Object(target);
  
        for (var index = 1; index < arguments.length; index++) {
          var nextSource = arguments[index];
  
          if (nextSource != null) { // Skip over if undefined or null
            for (var nextKey in nextSource) {
              // Avoid bugs when hasOwnProperty is shadowed
              if (Object.prototype.hasOwnProperty.call(nextSource, nextKey)) {
                to[nextKey] = nextSource[nextKey];
              }
            }
          }
        }
        return to;
      },
      writable: true,
      configurable: true
    });
  }

  // Thanks to: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Math/log10
  //  Christian: Added to support Math.log10(...) method for IE11
  Math.log10 = Math.log10 || function(x) {
    return Math.log(x) * Math.LOG10E;
  };

  // Thanks to: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/endsWith
  //  Christian: Added to support the String method endsWith(...)
  if (!String.prototype.endsWith) {
    String.prototype.endsWith = function(search, this_len) {
      if (this_len === undefined || this_len > this.length) {
        this_len = this.length;
      }
      return this.substring(this_len - search.length, this_len) === search;
    };
  }

  // Thank to: https://developer.mozilla.org/en-US/docs/Web/API/ChildNode/remove
  //  from:https://github.com/jserz/js_piece/blob/master/DOM/ChildNode/remove()/remove().md
  //  Christian: Added to support the remove(...) method of HTML Element nodes
(function (arr) {
  arr.forEach(function (item) {
    if (item.hasOwnProperty('remove')) {
      return;
    }
    Object.defineProperty(item, 'remove', {
      configurable: true,
      enumerable: true,
      writable: true,
      value: function remove() {
        if (this.parentNode !== null)
          this.parentNode.removeChild(this);
      }
    });
  });
})([Element.prototype, CharacterData.prototype, DocumentType.prototype]);
}


/**
 * -------------- Data Handlers --------------
 */
/**
 * elem: The element can be a DOM element, or the object ID of a WObject
 * event: must be an object which indicates also the JavaScript event and event target
 * args: array of args to pass into the Wt function
 */
SpectrumChartD3.prototype.WtEmit = function(elem, event) {
  if (!window.Wt) {
    console.warn('Wt not found! Canceling "' + event.name + '" emit function...');
    return;
  }

  //console.log( 'Emitting Wt event "' + ((event && event.name) ? event.name : 'null') + '", with ' + SpectrumChartD3.prototype.WtEmit.length + " arguments");

  // To support ES5 syntax in IE11, we replace spread operator with this
  var args = Array.prototype.slice.call(arguments, SpectrumChartD3.prototype.WtEmit.length);

  // Emit the function to Wt
  // Wt.emit( elem, event, ...args);  // ES6 syntax
  Wt.emit.apply(Wt, [elem, event].concat(args));
}

SpectrumChartD3.prototype.dataPointDrag = function() {
  var self = this;
  return function(d) {
    registerKeyboardHandler(self.keydown());
    document.onselectstart = function() { return false; };
    self.selected = self.dragged = d;
    self.update(false); /* boolean set to false to indicate no animation needed */

  }
}

SpectrumChartD3.prototype.do_rebin = function() {
  var self = this;

  if( !this.rawData || !self.rawData.spectra || !self.rawData.spectra.length ) {
    return;
  }

  this.rawData.spectra.forEach(function(spectrum, spectrumi) {
    var newRebin = 1;
    spectrum.points = [];

    var firstRaw = self.displayed_raw_start(spectrum);
    var lastRaw = self.displayed_raw_end(spectrum);

    var npoints = lastRaw - firstRaw;
    if( npoints > 1 && self.size.width > 2 ) {
      newRebin = Math.ceil( self.options.spectrumLineWidth * npoints / (self.size.width) );
    }

    if( newRebin != spectrum.rebinFactor || self.firstRaw !== firstRaw || self.lastRaw !== lastRaw ){
      spectrum.points = [];

      if( spectrum.rebinFactor != newRebin ){
        var txt = self.options.ylabel ? self.options.ylabel : "";
        if( newRebin !== 1 )
          txt += " per " + newRebin + " Channels"
        self.vis.select(".yaxistitle").text( txt );
      }

      spectrum.rebinFactor = newRebin;
      spectrum.firstRaw = firstRaw;
      spectrum.lastRaw = lastRaw;

      /*Round firstRaw and lastRaw down and up to even multiples of newRebin */
      firstRaw -= (firstRaw % newRebin);
      lastRaw += newRebin - (lastRaw % newRebin);
      if( firstRaw >= newRebin )
        firstRaw -= newRebin;
      if( lastRaw > spectrum.x.length )
        lastRaw = spectrum.x.length;


      /*could do some optimizations here where we actually do a slightly larger */
      /*  range than displayed, so that next time we might not have to go back */
      /*  through the data to recompute things (it isnt clear if D3 will plot */
      /*  these datas, should check on this.) */
      /*Also, could _maybe_ use energy range, rather than indexes to track if we */
      /*  need to rebin the data or not... */

      /*console.log( "self.rebinFactor=" + self.rebinFactor ); */

      for( var i = firstRaw; i < lastRaw; i += newRebin ){
        var thisdata = { };
        if (i >= spectrum.x.length) {
          thisdata['x'] = spectrum.x[spectrum.x.length-1];
        }
        else
          thisdata['x'] = spectrum.x[i];

        if (spectrum.y.length > 0) {
          var key = 'y';
          thisdata[key] = 0;
          for( var j = 0; j < newRebin && i+j<spectrum.y.length; ++j )
            thisdata[key] += spectrum.y[i+j];
          thisdata[key] *= spectrum.yScaleFactor;
        }
        spectrum.points.push( thisdata );
      }
    }
  });
}

SpectrumChartD3.prototype.rebinSpectrum = function(spectrumToBeAdjusted, linei) {
  var self = this;

  if( !this.rawData || !this.rawData.spectra || !this.rawData.spectra.length ) 
    return;

  /* Check for the which corresponding spectrum line is the specified one to be rebinned */
  if (linei == null || !spectrumToBeAdjusted) 
    return;

  var newRebin = 1;

  var firstRaw = self.displayed_raw_start(spectrumToBeAdjusted);
  var lastRaw = self.displayed_raw_end(spectrumToBeAdjusted);

  var npoints = lastRaw - firstRaw;
  if( npoints > 1 && this.size.width > 2 )
    newRebin = Math.ceil( npoints / this.size.width );

  /* Since we can only adjust scale factors for background/secondary/others, we don't need to adjust y-axis title */
  /*
  if( spectrumToBeAdjusted.rebinFactor != newRebin ){
    var txt = this.options.ylabel ? this.options.ylabel : "";
    if( newRebin !== 1 )
      txt += " per " + newRebin + " Channels"
    d3.select(".yaxistitle").text( txt );
  }
  */

  spectrumToBeAdjusted.rebinFactor = newRebin;
  spectrumToBeAdjusted.firstRaw = firstRaw;
  spectrumToBeAdjusted.lastRaw = lastRaw;

  /*Round firstRaw and lastRaw down and up to even multiples of newRebin */
  firstRaw -= (firstRaw % newRebin);
  lastRaw += newRebin - (lastRaw % newRebin);
  if( firstRaw >= newRebin )
    firstRaw -= newRebin;
  if( lastRaw > spectrumToBeAdjusted.x.length )
    lastRaw = spectrumToBeAdjusted.x.length;


  /*could do some optimizations here where we actually do a slightly larger */
  /*  range than displayed, so that next time we might not have to go back */
  /*  through the data to recompute things (it isnt clear if D3 will plot */
  /*  these datas, should check on this.) */
  /*Also, could _maybe_ use energy range, rather than indexes to track if we */
  /*  need to rebin the data or not... */

  /*console.log( "self.rebinFactor=" + self.rebinFactor ); */
  var i = firstRaw;
  for( var pointi = 0; pointi < spectrumToBeAdjusted.points.length; pointi++ ){
    var thisdata = spectrumToBeAdjusted.points[pointi];

    if( spectrumToBeAdjusted.y.length > 0 ) {
      thisdata.y = 0;
      for( var j = 0; j < newRebin && i+j<spectrumToBeAdjusted.y.length; ++j )
        thisdata.y += spectrumToBeAdjusted.y[i+j];
      thisdata.y *= spectrumToBeAdjusted.yScaleFactor;
    }

    i += newRebin;
  }
}

/**
 * Adds or replaces the first spectrum seen with the passed-in type in the raw data with new spectrum data.
 */
SpectrumChartD3.prototype.setSpectrumData = function( spectrumData, resetdomain, spectrumType, id, backgroundID ) {
  var self = this;

  if (!spectrumData) return;
  if (!spectrumType || !(spectrumType in self.spectrumTypes)) return;

  if (!self.rawData) self.rawData = { updateTime: spectrumData.updateTime, spectra: [] };
  if (!self.rawData.updateTime) self.rawData.updateTime = spectrumData.updateTime;

  let spectra = self.rawData.spectra;
  let index = -1;
  spectrumData = spectrumData.spectra[0];

  //console.log('setting ', spectrumData);

  // Set the ID if it was specified
  if (typeof id !== 'undefined') spectrumData.id = id;
  if( spectrumData.id === 'undefined' || spectrumData.id === null ) spectrumData.id = Math.random();

  // Set the background ID if it was specified
  if (backgroundID) spectrumData.backgroundID = backgroundID;

  // Find index of first spectrum of this type
  for (let i = 0; i < spectra.length; i++) {
    if (spectra[i].type === spectrumType) {
      index = i;
      break;
    }
  }

  if (index < 0) {  // no spectrum of this type found, so add it onto raw data
    spectra.push(spectrumData);

  } else {  // spectrum found of this type, so replace it
    spectra[index] = spectrumData;
  }

  // Call primary function for setting data
  self.setData( self.rawData, resetdomain );
}

SpectrumChartD3.prototype.removeSpectrumData = function( resetdomain, spectrumType ) {
  /* Temporary depreciated function. */
  this.removeSpectrumDataByType( resetdomain, spectrumType );
}

/** Removes all spectra seen with the passed-in type in the raw data. */
SpectrumChartD3.prototype.removeSpectrumDataByType = function( resetdomain, spectrumType ) {
  var self = this;

  if (!spectrumType || !(spectrumType in self.spectrumTypes)) return;
  if (!self.rawData) self.rawData = { spectra: [] };

  let spectra = self.rawData.spectra;

  // Find index of first spectrum of this type
  let havemore = true;
  while( havemore && spectra.length > 0 ) {
    havemore = false;
    for (let i = 0; i < spectra.length; i++) {
      if (spectra[i].type === spectrumType) {
        havemore = true;
        spectra.splice(i, 1);
        break;
      }
    }
  }
  
  // Call primary function for setting data
  self.setData( self.rawData, resetdomain );
}

SpectrumChartD3.prototype.setData = function( data, resetdomain ) {
  // ToDo: need to make some consistency checks on data here
  /*  - Has all necassary variables */
  /*  - Energy is monotonically increasing */
  /*  - All y's are the same length, and consistent with x. */
  /*  - No infs or nans. */

  var self = this;

  
  //Remove all the lines for the current drawn histograms
  this.vis.selectAll(".speclinepath").remove();

  this.vis.selectAll('path.line').remove();
  if (this.sliderChart) this.sliderChart.selectAll('.sliderLine').remove(); // Clear x-axis slider chart lines if present

  this.rawData = null;
  this.firstRaw = this.lastRaw = this.rebinFactor = -1; /*force rebin calc */

  try
  {
    if( !data || !data.spectra ) throw null;
    if( !Array.isArray(data.spectra) || data.spectra.length < 1 )
      throw 'No spectrum-data specified';
    /*check that x is same length or one longer than y. */
    /*Check that all specified y's are the same length */
  }catch(e){
    //if(e) console.log(e);

    // Christian [05122018]: Added other necessary display render methods to ensure consistency even when chart has no data
    //this.options.scaleBackgroundSecondary = false;
    this.updateLegend();
   
    this.redraw()();
    return;
  }

  this.rawData = data;

  this.rawData.spectra.forEach( function(spectrum,i){
    if( !spectrum || !spectrum.y.length )
      return;
    if( spectrum.xeqn && spectrum.xeqn.length>1 && !spectrum.x && spectrum.y && spectrum.y.length )
    {
      /* A polynomial equation was specified, rather than lower channel energies */
      spectrum.x = [];
      for( var i = 0; i < spectrum.y.length; ++i )
      {
        spectrum.x[i] = spectrum.xeqn[0];
        for( var j = 1; j < spectrum.xeqn.length; ++j )
          spectrum.x[i] += spectrum.xeqn[j] * Math.pow(i,j);
      }
    }
  } );
  
  for (var i = 0; i < this.rawData.spectra.length; ++i)
    this['line'+i] = null;
  
  this.do_rebin();  /*this doesnt appear to be necassay, but JIC */

  /*Make it so the x-axis shows all the data */
  if( resetdomain ) {
    var bounds = self.min_max_x_values();
    var minx = bounds[0], maxx = bounds[1];
    
    this.setXAxisRange(minx, maxx, true);
  }

  /*reset the zoom, so first userzoom action wont behave wierdly */
  /* this.zoom.x(this.xScale); */
  /* this.zoom.y(this.yScale); */

  /* Hack: To properly choose the right set of points for the y-axis points */
  function y(line) {
    return function(d) {
      var y = self.yScale(d['y']);
      if (isNaN(y)) y = 0;
      return y; 
    }
  }

  var maxYScaleFactor = 0.1;
  for (var i = 0; i < this.rawData.spectra.length; ++i)
    this.rawData.spectra[i].dataSum = 0;

  /* Create the lines
    We want to draw the background first, then the secondary spectrum, then the primaries. There is probably a better way to do this,
    but for the moment well just brute force it.
  */
  let dataindexes = [[],[],[],[]], drawindexes = [];
  for( let i = 0; i < data.spectra.length; ++i ) {
    var type = data.spectra[i].type;
    if( type === self.spectrumTypes.BACKGROUND ){
      dataindexes[0].push(i);
    }else if( type === self.spectrumTypes.SECONDARY ){
      dataindexes[1].push(i);
    }else if( type === self.spectrumTypes.FOREGROUND ){
      dataindexes[3].push(i);
    }else {
      dataindexes[2].push(i);
    }
  }
  //flaten out dataindexes into a single 1D array.
  for( let i = 0; i < 4; ++i ) {
    for( let j = 0; j < dataindexes[i].length; ++j ){
      drawindexes.push(dataindexes[i][j]);
    }
  }
  
  for( let ind = 0; ind < drawindexes.length; ++ind ) {
    let i = drawindexes[ind];
    var spectrum = data.spectra[i];
    if (!spectrum.lineColor) spectrum.lineColor = self.getRandomColor();  // Set line color if not yet set
    if (!spectrum.peakColor) spectrum.peakColor = self.getRandomColor();  // Set peak color if not yet set
    if (spectrum.y.length) {
      for (var j = 0; j < spectrum.y.length; ++j) {
        spectrum.dataSum += spectrum.y[j];
      }
      this['line' + i] = d3.svg.line()
        .interpolate("step-after")
        .x( function(d, pi) {
          return self.xScale(d.x);
        })
        .y( y(i) );

      this.chartBody.append("path")
        .attr("id", "spectrumline"+i)
        .attr("class", "speclinepath")
        .attr("stroke-width", self.options.spectrumLineWidth)
        .attr("fill", 'none' )
        .attr("stroke", spectrum.lineColor ? spectrum.lineColor : 'black')
        .attr("d", this['line' + i](spectrum.points));

      if (spectrum.yScaleFactor)
        maxYScaleFactor = Math.max(spectrum.yScaleFactor, maxYScaleFactor);
    }
  }

  /* + 10 to add at keast some padding for scale */
  self.options.maxScaleFactor = maxYScaleFactor + 10;
  var maxsfinput;
  if (maxsfinput = document.getElementById("max-sf")) {
    maxsfinput.value = self.options.maxScaleFactor;
  }

  function needsDecimal(num) {
    return num % 1 != 0;
  }

  /* Update the spectrum drop down for adjusting y-scale factors */
  if (currentsftitle = document.getElementById("current-sf-title")) {
    var titles = self.getSpectrumTitles();
    currentsftitle.options.length = titles.length;
    titles.forEach(function(title,i) {
      if (i == 0)
        currentsftitle.options[i] = new Option("None", "", true, false);
      else
        currentsftitle.options[i] = new Option(title, title, false, false);
    });
  }

  this.addMouseInfoBox();

  this.updateLegend();
  this.drawScalerBackgroundSecondary();

  this.redraw()();
}

/** Sets (replacing any existing) peak data for first spectrum matching spectrumType
  Input should be like [{...},{...}]
 */
SpectrumChartD3.prototype.setRoiData = function( peak_data, spectrumType ) {
  let self = this;
  let hasset = false;
  
  if( !this.rawData || !this.rawData.spectra || !this.rawData.spectra )
    return;
  
  this.rawData.spectra.forEach( function(spectrum, i) {
    if( hasset || !spectrum || spectrum.type !== spectrumType )
      return;
    
    self.handleCancelRoiDrag();
    spectrum.peaks = peak_data;
    hasset = true;
  } );
  
  this.redraw()();
};


/**
 * Render/Drawing Functions
 */
SpectrumChartD3.prototype.update = function() {
  var self = this;

  if (!this.rawData || !this.rawData.spectra || !this.rawData.spectra.length)
    return;

  // Figure out which set of points to use
  //  Use background subtract if we're in that view mode, otherwise use the normal set of points
  const key = this.options.backgroundSubtract ? 'bgsubtractpoints' : 'points';

  this.rawData.spectra.forEach(function(spectrum, i) {
    var line = self.vis.select("#spectrumline"+i);
  
    if (spectrum.type === self.spectrumTypes.BACKGROUND) {
      line.attr('visibility', self.options.backgroundSubtract ? 'hidden' : 'visible');
      if (self.options.backgroundSubtract) return;
    }
    line.attr("d", self['line'+i](self.rawData.spectra[i][key]));
  });

  /*
  if( self.xrange !== self.xScale.range() ) {
    console.log( "xrange changed changed" );
  }

  if( self.xdomain !== self.xScale.domain() ) {
    console.log( "xrange domain changed" );
  }

  if( self.yrange !== self.yScale.range() ) {
    console.log( "yrange range changed" );
  }

  if( self.ydomain !== self.yScale.domain() ) {
    console.log( "yrange domain changed" );
  }

  if( self.prevRebinFactor !== this.rebinFactor ) {
    console.log( "rebin factor changed" );
  }

  self.prevRebinFactor = this.rebinFactor;
  self.xrange = self.xScale.range();   
  self.xdomain = self.xScale.domain(); 
  self.yrange = self.yScale.range();  
  self.ydomain = self.yScale.domain();
  */

  if (d3.event && d3.event.keyCode) {
    d3.event.preventDefault();
    d3.event.stopPropagation();
  }
}

SpectrumChartD3.prototype.redraw = function() {
  var self = this;

  return function() {
    
    if( this.size && (this.size.nYScalers !== this.numYScalers()) ) {
      this.handleResize( true );
    }
    
    self.do_rebin();
    self.rebinForBackgroundSubtract();  // Get the points for background subtract
    self.setYAxisDomain();

    var tx = function(d) { return "translate(" + self.xScale(d) + ",0)"; };
    var stroke = function(d) { return d ? "#ccc" : "#666"; };

    self.yAxis.scale(self.yScale);
    self.yAxisBody.call(self.yAxis);

    /**
     * Christian [032818]: Another perforance optimization. Assign style and event listeners 
     * for only major y-label ticks. This lessens the load and we can see a lot of improvement
     * in application to InterSpec and other high performing apps.
     */
    self.svg.selectAll('.yaxislabel')
      .each(function(d, i) {
        const label = d3.select(this);
        if (label.text().trim()) {  // If this y-label tick is a major tick
          label.style("cursor", "ns-resize")
            .on("mouseover", function(d) { d3.select(this).style("font-weight", "bold");})
            .on("mouseout",  function(d) { d3.select(this).style("font-weight", null);})
            .on("mousedown.drag",  self.yaxisDrag());

          if (self.isTouchDevice())
            label.on("touchstart.drag", self.yaxisDrag());
        }
      });

    if (self.options.showXAxisSliderChart) { self.drawXAxisSliderChart(); } 
    else                                   { self.cancelXAxisSliderChart(); }

    self.drawYTicks();
    
    self.calcLeftPadding( true );
    
    self.drawXTicks();

    self.drawXAxisArrows();

    /*The oringal code had the follwoing in, but I dont think is needed */
    /*self.plot.call(d3.behavior.zoom().x(self.xScale).y(self.yScale).on("zoom", self.redraw()));     */
    
    self.drawPeaks();
    self.drawSearchRanges();
    self.drawHighlightRegions();
    self.drawRefGammaLines();
    self.updateMouseCoordText();

    self.update();

    self.yAxisZoomedOutFully = true;
    /* console.log('yaxis domain = ', self.yScale.domain()); */
  }
}

SpectrumChartD3.prototype.calcLeftPadding = function( updategeom ){
  
  if( !this.options.adjustYAxisPadding ) {
    this.padding.leftComputed = this.padding.left; 
    return;
  }
  
  var labels = this.vis.selectAll("g.y").selectAll("text");
  
  var labelw = 4;
  labels.forEach( function(label){
    labelw = Math.max( labelw, label.parentNode.getBBox().width );
  });
  
  var labelpad = this.padding.labelPad;
  var ticklen = 7; /*hardcoded as major tick x1 */
  var title = this.svg.select(".yaxistitle");
  if( title )
    title.attr("transform","translate(-" + (labelw+labelpad) + " " + this.size.height/2+") rotate(-90)");
  
  var newleft = ticklen + labelw + labelpad + this.padding.left + 4;
  
  if( !updategeom ) {
    this.padding.leftComputed = newleft;
  } else if( Math.abs(this.padding.leftComputed - newleft) > 1.0 ) {
    this.padding.leftComputed = newleft;
    this.handleResize( true );
  } 
}

/* Sets the title of the graph */
SpectrumChartD3.prototype.setTitle = function(title,dontRedraw) {
  var titleh = 0;
  if( (title == null || typeof title !== 'string') || title.length === 0 ){
    this.options.title = null;
    this.svg.select('#chartTitle').remove();
  } else {
    if( this.options.title )
      titleh = this.svg.selectAll(".title").text( title ).node().getBBox().height;
    else
      titleh = this.svg.append("text")
          .attr("id", "chartTitle")
          .attr("class", "title")
          .text(title)
          .attr("x", this.cx/2)
          .attr("dy", this.padding.title)
          .style("text-anchor","middle")
          .node().getBBox().height;
    this.options.title = title;
  }
  this.handleResize( dontRedraw ); 
  this.refreshRefGammaLines();
}

SpectrumChartD3.prototype.setXAxisTitle = function(title) {
  var self = this;

  self.options.xlabel = null;
  self.svg.select('.xaxistitle').remove();

  if( (title == null || typeof title !== 'string') || title.length === 0 )
    return;
  
  self.options.xlabel = title;
  self.xaxistitle = self.svg.append("text")
    .attr("class", "xaxistitle")
    .text(self.options.xlabel)
    .attr("x", self.size.width/2)
    .attr("y", self.size.height )
    .attr("dy",29)
    .style("text-anchor","middle");

  self.handleResize( false );
}

SpectrumChartD3.prototype.setYAxisTitle = function(title) {
  var self = this;

  self.options.ylabel = null;
  self.vis.select('#yaxistitle-container').remove();

  if( (title == null || typeof title !== 'string') || title.length === 0 )
    return;
  
  self.options.ylabel = title;
  self.vis.append("g")
    .attr('id', 'yaxistitle-container')
    .append("text")
      .attr("class", "yaxistitle")
      .text(self.options.ylabel + (self.rebinFactor > 1 ? (" per " + self.rebinFactor + " Channels") : "") )
      .style("text-anchor","middle");

  self.handleResize( true );
}

SpectrumChartD3.prototype.handleZoom = function() {
  var self = this;

  function shouldZoomInX() {
    var keys = Object.keys(self.touchesOnChart);

    if (keys.length == 1) {
      var touch = self.touchesOnChart[keys[0]];
      var x0 = Math.round( touch.startX );
      var x1 = Math.round( touch.pageX );
      return Math.abs(x0-x1)>=15;
    }
    else if (keys.length == 0 || keys.length > 2)
      return false;

    var touch1 = self.touchesOnChart[keys[0]];
    var touch2 = self.touchesOnChart[keys[1]];
    var adx1 = Math.abs( touch1.startX - touch2.startX );
    var adx2 = Math.abs( touch1.pageX  - touch2.pageX );
    var ady1 = Math.abs( touch1.startY - touch2.startY );
    var ady2 = Math.abs( touch1.pageY  - touch2.pageY );
    var ddx = Math.abs( adx2 - adx1 );
    var ddy = Math.abs( ady2 - ady1 );
    var areVertical = (adx2 > ady2);

    return (ddx >= ddy && ddx>20);
  }

  return function() {
    /* console.log( 'handleZoom' ); */
    var e = d3.event;
    var t = d3.touches(self.vis[0][0]);

    /* Two touches are close together if distance between two touches < 70px */
    /*    We want to cancel the zoom if this is true to prevent redrawing while detecting swipes (may need to change/remove this) */
    var areTwoTouchesCloseTogether = t.length === 2 && self.dist(t[0], t[1]) < 70; 

    if (e && e.sourceEvent && e.sourceEvent.type.startsWith("mouse")) {
      self.redraw()();
      return;
    }

    /* Awesome hack: saving the zoom scale and translation allows us to prevent double-tap zooming! */
    if (d3.event.sourceEvent === null || d3.event.sourceEvent.touches == 1 || areTwoTouchesCloseTogether ||
          self.deletePeakSwipe || self.controlDragSwipe || self.altShiftSwipe || self.zoomInYPinch || !shouldZoomInX()) {
      const domain = self.xScale.domain();
      
      self.setXAxisRange(domain[0], domain[1], true);
      self.zoom.scale(self.savedZoomScale);
      self.zoom.translate(self.savedZoomTranslation);
      return false;
    }

    /* Get chart domain values */
    var xaxismin,
        xaxismax,
        bounds,
        x0 = self.xScale.domain()[0],
        x1 = self.xScale.domain()[1];

    /* Set the proper min/max chart values w/respect to data */
    if (!self.rawData || !self.rawData.spectra || !self.rawData.spectra.length) {
      xaxismin = 0;
      xaxismax = 3000;
    } else {
      bounds = self.min_max_x_values();
      xaxismin = bounds[0];
      xaxismax = bounds[1];
    }

    /* Adjust domains properly to min/max chart values */
    if( x0 < xaxismin ){
      x1 += xaxismin - x0;
    }else if( x1 > xaxismax ){
      x0 -= x1 - xaxismax;
    }
      
    /* Set the x domain values */
    x0 = Math.max( x0, xaxismin );
    x1 = Math.min( x1, xaxismax);

    /* Update the x-domain to the new zoomed in values */
    self.setXAxisRange(x0, x1, true);

    /* Don't redraw (abort the function) if the domain did not change from last time */
    /*    Needed to add toPrecision(4) because domain would change (very) slightly sometimes  */
    if (self.previousX0 && self.previousX1 && 
        (x0.toPrecision(4) === self.previousX0.toPrecision(4) && x1.toPrecision(4) === self.previousX1.toPrecision(4))) {
      return false;
    }

    /* Set previous domain values to current ones */
    self.previousX0 = x0;
    self.previousX1 = x1;

    /* Redraw the chart */
    self.redraw()();
  }
}

SpectrumChartD3.prototype.handleZoomEnd = function () {
  var self = this;

  return function() {

      /* Reset the d3 zoom vector so next zoom action will be independant of this one */
      self.zoom.x(self.xScale);
      self.zoom.y(self.yScale);
  };
}

SpectrumChartD3.prototype.handleResize = function( dontRedraw ) {
  var self = this;

  const prevCx = this.cx;
  const prevCy = this.cy;
  
  this.cx = this.chart.clientWidth;
  this.cy = this.chart.clientHeight;
  
  var titleh = 0, xtitleh = 0, xlabelh = 7 + 22;
  if( this.options.title ) {
    this.svg.selectAll(".title").forEach( function(t){
      titleh = t[0].getBBox().height;  
   });
  }
  
  if( this.xaxistitle )
    xtitleh = this.xaxistitle.node().getBBox().height;
  
  /*Below isnt quite working, so stick with estimate of 22 above */
  /*self.xAxisBody.selectAll('g.tick').forEach( function(t){ */
      /*console.log( t[0].getBBox().height );  /*sometimes gives 22.21875, sometimes 4 */
   /*}); */
  
  this.padding.topComputed = titleh + this.padding.top + (titleh > 0 ? this.padding.titlePad : 0);
  
  /*Not sure where the -12 comes from, but things seem to work out... */
  if( this.options.compactXAxis && xtitleh > 0 ) {
    var txth = 4 + this.padding.xTitlePad + xtitleh;
    this.padding.bottomComputed = this.padding.bottom + Math.max( txth, xlabelh-10 );
  } else {
    this.padding.bottomComputed = -12 + this.padding.bottom + xlabelh + (xtitleh > 0 ? this.padding.xTitlePad : 0) + xtitleh; 
  }
  
  this.calcLeftPadding( false );
  
  if( self.sliderChartPlot ) {
    let ypad = self.padding.sliderChart + this.padding.topComputed + this.padding.bottomComputed;
    this.size.sliderChartHeight = Math.max( 0, self.options.sliderChartHeightFraction*(this.cy - ypad) );
    this.size.sliderChartWidth = Math.max(0.85*this.cx,this.cx-100);
  } else {
    this.size.sliderChartHeight = 0;
  }
 
  this.size.nYScalers = this.numYScalers();
  this.size.width = Math.max(0, this.cx - this.padding.leftComputed - this.padding.right - 20*this.size.nYScalers);
  this.size.height = Math.max(0, this.cy - this.padding.topComputed - this.padding.bottomComputed - this.size.sliderChartHeight);

  this.xScale.range([0, this.size.width]);
  this.vis.attr("width",  this.size.width)
          .attr("height", this.size.height);
  this.vis.attr("transform", "translate(" + this.padding.leftComputed + "," + this.padding.topComputed + ")");
  this.plot.attr("width", this.size.width)
           .attr("height", this.size.height);

  self.svg
      .attr("width", this.cx)
      .attr("height", this.cy)
      .attr("viewBox", "0 0 "+this.cx+" "+this.cy);

  this.vis.attr("width", this.cx )
          .attr("height", this.cy );

  d3.select("#chartarea"+this.chart.id)
          .attr("width", this.size.width )
          .attr("height", this.size.height );

  d3.select("#clip"+ this.chart.id).select("rect")
    .attr("width", this.size.width )
    .attr("height", this.size.height );

  /*Fix the text position */
  this.svg.selectAll(".title")
      .attr("x", this.cx/2);

  if( this.xaxistitle ){
    if( !this.options.compactXAxis ){
      this.xaxistitle.attr("x", this.cx/2);
      this.xaxistitle.attr("dy",xlabelh+this.padding.xTitlePad + (this.options.title ? 33 : 6)); /* Christian: hard-coded 33 to account for padding between x-axis labels and slider chart */

    } else {
      this.xaxistitle.attr("x", this.size.width - this.xaxistitle.node().getBBox().width + 30 );  /*Not certain why this 30 is needed (I'm probably leaving out some element) but necassary to have label line up right */
      this.xaxistitle.attr("dy",xtitleh + this.padding.xTitlePad + (this.options.title ? 31 : 4));
    }
    this.xaxistitle.attr("y", this.size.height);
  }

 /* this.vis.selectAll(".yaxistitle") */
    /* .attr("transform","translate(" + -40 + " " + this.size.height/2+") rotate(-90)"); */
  this.xAxisBody.attr("width", this.size.width )
                .attr("height", this.size.height )
                .attr("transform", "translate(0," + this.size.height + ")");

  // Christian: Prevents bug of initially rendering chart w/all ticks displayed 
  if (this.cx !== prevCx && this.cy !== prevCy)
    this.xAxisBody.call(this.xAxis);

  this.yAxisBody.attr("height", this.size.height )
                .call(this.yAxis);
  
  this.refLineInfo.select("circle").attr("cy", this.size.height);
  this.mouseInfo.attr("transform","translate(" + this.size.width + "," + this.size.height + ")");

  if( this.xGrid ) {
    this.xGrid.innerTickSize(-this.size.height)
    this.xGridBody.attr("width", this.size.width )
        .attr("height", this.size.height )
        .attr("transform", "translate(0," + this.size.height + ")")
        .call(this.xGrid);
  }

  if( this.yGrid ) {
    this.yGrid.innerTickSize(-this.size.width)
    this.yGridBody.attr("width", this.size.width )
        .attr("height", this.size.height )
        .attr("transform", "translate(0,0)")
        .call(this.yGrid);
  }
  
  /*Make sure the legend stays visible */
  if( this.legend && this.size.height > 50 && this.size.width > 100 && prevCx > 50 && prevCy > 50 ) {
    var trans = d3.transform(this.legend.attr("transform")).translate;
    var bb = this.legendBox.node().getBBox();
    
    //If legend is closer to left side, keep distance to left of chart the same, else right.
    //Same for top/bottom.  Usses upper left of legend, and not center... oh well.
    var legx = (trans[0] < 0.5*prevCx) ? trans[0] : this.cx - (prevCx - trans[0]);
    var legy = (trans[1] < 0.5*prevCy) ? trans[1] : this.cy - (prevCy - trans[1]);
    
    //Make sure legend is visible
    legx = ((legx+bb.width) > this.cx) ? (this.cx - bb.width - this.padding.right - 20*this.size.nYScalers) : legx;
    legy = ((legy+bb.height) > this.cy) ? (this.cy - bb.height) : legy;
    
    this.legend.attr("transform", "translate(" + Math.max(0,legx) + "," + Math.max(legy,0) + ")" );
  }

  if (this.options.showXAxisSliderChart) { self.drawXAxisSliderChart(); } 
  else                                   { self.cancelXAxisSliderChart(); }
  
  this.xScale.range([0, this.size.width]);
  this.yScale.range([0, this.size.height]);

  this.drawScalerBackgroundSecondary();
  
  /* this.zoom.x(this.xScale); */
  /* this.zoom.y(this.yScale); */

  if( !dontRedraw ) {
    this.setData( this.rawData, false );
    this.redraw()();
  }
}

/* Pan chart is called when right-click dragging */
SpectrumChartD3.prototype.handlePanChart = function () {
  var self = this;

  var minx, maxx, bounds;
  if( !self.rawData || !self.rawData.spectra || !self.rawData.spectra.length ){
    minx = 0;
    maxx = 3000;
  }else {
    bounds = self.min_max_x_values();
    minx = bounds[0];
    maxx = bounds[1];
  }

  /* We are now right click dragging  */
  self.rightClickDrag = true;

  /* For some reason, using the mouse position for self.vis makes panning slightly buggy, so I'm using the document body coordinates instead */
  var docMouse = d3.mouse(document.body);

  if (!docMouse || !self.rightClickDown)
    return;

  d3.select(document.body).attr("cursor", "pointer");

  /* Set the pan right / pan left booleans */
  var panRight = docMouse[0] < self.rightClickDown[0],   /* pan right if current mouse position to the left from previous mouse position */
      panLeft = docMouse[0] > self.rightClickDown[0],    /* pan left if current mouse position to the right from previous mouse position */
      dx = 0;

  function newXDomain() {
    var currentX = docMouse[0],
        delta = currentX - self.rightClickDown[0],
        oldMin = self.xScale.range()[0],
        oldMax = self.xScale.range()[1];

    /* Declare new x domain members */
    var newXMin = oldMin, 
        newXMax = oldMax;

    newXMin = oldMin - delta;
    newXMax = oldMax - delta;

    newXMin = self.xScale.invert(newXMin);
    newXMax = self.xScale.invert(newXMax);

    /* Make sure we don't go set the domain out of bounds from the data */
    if( newXMin < minx ){
     newXMax += (minx - newXMin);
     newXMin = minx; 
    }
    if( newXMax > maxx ){
     newXMin = Math.max(minx,newXMin-(newXMax-maxx));
     newXMax = maxx;
    }
    return [newXMin, newXMax];
  }

  /* Get the new x values */
  var newXMin = newXDomain()[0],
      newXMax = newXDomain()[1];

  /* Pan the chart */
  self.setXAxisRange(newXMin, newXMax, false);
  self.redraw()();

  /* New mouse position set to current moue position */
  self.rightClickDown = docMouse;
}


/**
 * -------------- Chart Event Handlers --------------
 */
SpectrumChartD3.prototype.handleChartMouseMove = function() {
  var self = this;

  return function() {
    self.mousemove()();

    /* If no data is detected, then stop updating other mouse move parameters */
    if(!self.rawData || !self.rawData.spectra || !self.rawData.spectra.length || self.xaxisdown || !isNaN(self.yaxisdown) || self.legdown )
      return;

    /* Prevent and stop default events from ocurring */
    d3.event.preventDefault();
    d3.event.stopPropagation();

    /* Get the absoulate minimum and maximum x-values valid in the data */
    var minx, maxx, bounds;
    if( !self.rawData || !self.rawData.spectra || !self.rawData.spectra.length ){
      minx = 0;
      maxx = 3000;
    }else {
      bounds = self.min_max_x_values();
      minx = bounds[0];
      maxx = bounds[1];
    }
     
    /* Set the mouse and chart parameters */
    var m;

    m = d3.mouse(self.vis[0][0]);
    x0_min = self.xScale.range()[0];
    x1_max = self.xScale.range()[1];
    self.lastMouseMovePos = m;

    var x = m[0], y = m[1];

    /* Adjust the last mouse move position in case user starts draggin from out of bounds */
    if (self.lastMouseMovePos[1] < 0)
      self.lastMouseMovePos[1] = 0;
    else if (self.lastMouseMovePos[1] > self.size.height)
      self.lastMouseMovePos[1] = self.size.height;

    /* Do any other mousemove events that could be triggered by the left mouse drag */
    self.handleMouseMoveSliderChart()();
    self.handleMouseMoveScaleFactorSlider()();

    /* It seems that d3.event.buttons is present on Chrome and Firefox, but is not in Safari. */
    /* d3.event.button is present in all browsers, but is a little less consistent so we need to keep track of when the left or right mouse is down. */
    if ((d3.event.button === 0 && self.leftMouseDown)) {        /* If left click being held down (left-click and drag) */
      const isWindows = self.isWindows();

      d3.select(document.body).attr("cursor", "move");

      /* Holding the Shift-key and left-click dragging --> Delete Peaks Mode */
      self.isDeletingPeaks = d3.event.shiftKey && !d3.event.altKey && !d3.event.ctrlKey && !d3.event.metaKey && !self.fittingPeak && !self.escapeKeyPressed;

      /* Holding the Alt+Shift-key and left-click dragging --> Count Gammas Mode */
      self.isCountingGammas = d3.event.altKey && d3.event.shiftKey && !d3.event.ctrlKey && !d3.event.metaKey && !self.fittingPeak && !self.escapeKeyPressed;

      /* Holding the Alt+Ctrl-key + Left-click Dragging --> Recalibration Mode */
      self.isRecalibrating = d3.event.altKey && d3.event.ctrlKey && !d3.event.metaKey && !d3.event.shiftKey && !self.fittingPeak && !self.escapeKeyPressed; 

      /* Holding the Command-key + Left-click dragging --> Zoom-in Y Mode */
      // For Windows, you can zoom-in on the y-axis using Alt + Left-drag
      self.isZoomingInYAxis = (isWindows ? d3.event.altKey : d3.event.metaKey) && !(isWindows ? d3.event.metaKey : d3.event.altKey) && !d3.event.ctrlKey && !d3.event.shiftKey && !self.fittingPeak && !self.escapeKeyPressed;

      /* Holding the Alt-key + Left-click dragging ---> Undefined, maybe a future implementation? */
      self.isUndefinedMouseAction = (isWindows ? d3.event.metaKey : d3.event.altKey) && !d3.event.ctrlKey && !(isWindows ? d3.event.altKey : d3.event.metaKey) && !d3.event.shiftKey && !self.fittingPeak && !self.escapeKeyPressed;

      var isZoomingInXAxis = !d3.event.altKey && !d3.event.ctrlKey && !d3.event.metaKey && !d3.event.shiftKey && !self.fittingPeak && !self.escapeKeyPressed && !self.roiIsBeingDragged;

      /* If erasing peaks */
      if( self.fittingPeak ) {          /* If fitting peaks */
        self.handleMouseMovePeakFit();
      } else if (self.isDeletingPeaks) {   /* If deleting peaks */
        self.handleMouseMoveDeletePeak();
      } else if (self.isCountingGammas) {   /* If counting gammas */
        self.handleMouseMoveCountGammas();
      } else if (self.isRecalibrating) {      /* If recalibrating the chart */
        self.handleMouseMoveRecalibration();
      } else if (self.isZoomingInYAxis) {        /* If zooming in y-axis */
        self.handleMouseMoveZoomInY();
      } else if (self.isUndefinedMouseAction) {   /* If undefined mouse action */
        self.handleCancelAllMouseEvents()();      /* Do nothing, save for future feature */
      } else if (isZoomingInXAxis) {    /* If zooming in x-axis */
        self.handleMouseMoveZoomInX();
      } else if( self.roiIsBeingDragged ){
        self.handleRoiDrag();
      } else {
        self.handleCancelAllMouseEvents()();
      }

      return;
    } else if ( self.rightClickDown ){
      self.handleCancelRoiDrag();

      /* Right Click Dragging: pans the chart left and right */
      self.handlePanChart();
    } else if( self.options.allowDragRoiExtent
               && self.rawData.spectra && self.rawData.spectra.length > 0
               && (x >= 0 && y >= 0 && y <= self.size.height && x <= self.size.width
               && !d3.event.altKey && !d3.event.ctrlKey && !d3.event.metaKey
               && !d3.event.shiftKey && !self.fittingPeak && !self.escapeKeyPressed ) ) {
      //Also check if we are between ymin and ymax of ROI....
      var onRoiEdge = false;
      
      //self.rawData.spectra[0].peaks.forEach( function(roi){
      self.peakPaths.forEach( function(info){
        if( onRoiEdge )
          return;

        var lpx = self.xScale(info.lowerEnergy);
        var upx = self.xScale(info.upperEnergy);
        
        //Dont create handles for to narrow of a range (make user zoom in a bit more)
        if( (upx-lpx) < 15 )
          return;

        var isOnLower = Math.abs(lpx-x) < 5;
        var isOnUpper = Math.abs(upx-x) < 5;
        if( !isOnLower && !isOnUpper )
          return;
        
        //Make mouse be within ROI in y.   Should draw handles/lines appropriately using roi.color
        if( info.yRangePx && info.yRangePx.length==2 && (y < (info.yRangePx[0]-10) || y > (0,info.yRangePx[1]+1)) )
          return;
        
        onRoiEdge = true;
        self.showRoiDragOption(info);
      });
      
      if( !onRoiEdge && self.roiDragBox && !self.roiIsBeingDragged ){
        self.handleCancelRoiDrag();
        d3.select('body').style("cursor", "default");
      }
    } else if( self.roiDragBox ){
      self.handleCancelRoiDrag();
      d3.select('body').style("cursor", "default");
    }//if / else {what to do}
      

    self.updateFeatureMarkers(-1);
  }
}


SpectrumChartD3.prototype.showRoiDragOption = function(info){
  let self = this;

  let roi = info.roi;
  
  if( !roi || d3.event.altKey || d3.event.ctrlKey || d3.event.metaKey
      || d3.event.shiftKey || self.escapeKeyPressed )
  {
    self.handleCancelRoiDrag();
    return;
  }
  
  let m = d3.mouse(self.vis[0][0]);
  let x = m[0], y = m[1];

  let lpx = self.xScale(roi.lowerEnergy);
  let upx = self.xScale(roi.upperEnergy);
  let isOnLower = Math.abs(lpx-x) < 5;

  self.roiBeingDragged = { roi: roi, yRangePx: info.yRangePx, color: (info.color ? info.color : 'black') };
  
  if( !self.roiDragBox ){
    
    //ToDo: put line and box inside of a <g> element and move it
    self.roiDragBox = this.vis.append("g");
    // .attr("width", 10 )
    // .attr("height", 10 )
    // .attr("class", "roiDragBox" )
    // .attr("transform", "translate(" + ((isOnLower ? lpx : upx) - 5) + "," + this.size.height + ")")
    
    const tickElement = document.querySelector('.tick');
    const tickStyle = tickElement ? getComputedStyle(tickElement) : null;
    let axiscolor = tickStyle && tickStyle.stroke ? tickStyle.stroke : 'black';
    self.roiBeingDragged.axiscolor = axiscolor;
    
    self.roiDragBox.append("rect")
            .attr("class", "roiDragBox")
            .attr("rx", 2)
            .attr("ry", 2)
            .attr("x", 0)
            .attr("y", 0)
            .attr("width", 10)
            .attr("height", 20)
            .attr("stroke", axiscolor )
            .attr("fill", axiscolor );

    //Add some lines inside the box for a little bit of texture
    for( x of [3,7] ){
      self.roiDragBox.append("line")
          .attr("class", "roiDragBoxLine")
          .attr("stroke-width", 0.85*self.options.spectrumLineWidth)
          .attr("x1", x).attr("x2", x)
          .attr("y1", 4).attr("y2", 16);
    }
    
    self.roiDragLine = self.vis.append("line")
            .attr("class", "roiDragLine");
  }

  d3.select('body').style("cursor", "ew-resize");

  let y1 = 0;
  let y2 = self.size.height
  
  if( info.yRangePx && info.yRangePx.length==2 ){
    y1 = Math.max(0,info.yRangePx[0]-10);
    y2 = Math.min(y2,info.yRangePx[1]+10);
  }
  
  self.roiDragBox.attr("transform", "translate(" + ((isOnLower ? lpx : upx) - 5.5) + "," + (-10 + y1 + 0.5*(y2-y1)) + ")");
  
  d3.selectAll('.roiDragBoxLine').forEach( function(line){
    for( var i = 0; i < line.length; ++i)
      d3.select(line[i]).attr("stroke", self.roiBeingDragged.color );
  } );
  
  //self.roiDragBox.attr("x", (isOnLower ? lpx : upx) - 5)
      //.attr("y", -10 + y1 + 0.5*(y2-y1));
      
  self.roiDragLine.attr("x1", (isOnLower ? lpx : upx) - 0.5)
      .attr("x2", (isOnLower ? lpx : upx) - 0.5)
      .attr("y1", y1)
      .attr("y2", y2)
      .attr("stroke", self.roiBeingDragged.color );

  //console.log( 'x=' + x + ", y=" + y + ", roi.lowerEnergy=" + roi.lowerEnergy + ", roi.upperEnergy=" + roi.upperEnergy );
};//showRoiDragOption()



SpectrumChartD3.prototype.handleRoiDrag = function(){
  //We have clicked the mouse down on the edge of a ROI, and now moved the mouse 
  //  - update roiDragBox location 
  let self = this;
  
  let m = d3.mouse(self.vis[0][0]);
  let x = m[0], y = m[1];

  
  if( d3.event.altKey || d3.event.ctrlKey || d3.event.metaKey
     || d3.event.shiftKey || self.escapeKeyPressed )
  {
    self.handleCancelRoiDrag();
    return;
  }
  
  //console.log( 'handleRoiDrag roiDragMouseDown ' + self.roiDragMouseDown );

  if( self.roiDragLastCoord && Math.abs(x-self.roiDragLastCoord[0]) < 1 )
    return;
        
  d3.select('body').style("cursor", "ew-resize");

  let roiinfo = self.roiBeingDragged;
  let roi = roiinfo.roi;
  let mdx = self.roiDragMouseDown; // [m[0], roiPx, energy, isLowerEdge];
  let xcenter = x + mdx[1] - mdx[0];  //having issue
  let energy = self.xScale.invert(xcenter);
  let counts = self.yScale.invert(y);
  let lowerEdgeDrag = mdx[3];
        
  self.roiDragLastCoord = [x,y,energy,counts];
  
  
  let y1 = 0;
  let y2 = self.size.height
  
  if( roiinfo.yRangePx && roiinfo.yRangePx.length==2 ){
    y1 = Math.max(0,roiinfo.yRangePx[0]-10);
    y2 = Math.min(y2,roiinfo.yRangePx[1]+10);
  }
  
  //self.roiDragBox
  //    .attr("x", xcenter - 5)
  //    .attr("y", -10 + y1 + 0.5*(y2-y1));
  self.roiDragBox.attr("transform", "translate(" + (xcenter - 5.5) + "," + (-10 + y1 + 0.5*(y2-y1)) + ")");
  
  self.roiDragLine
      .attr("x1", xcenter - 0.5)
      .attr("x2", xcenter - 0.5)
      .attr("y1", y1)
      .attr("y2", y2);


  //Emit current position, no more often than twice per second, or if there
  //  are no requests pending.
  let emitFcn = function(){
    self.roiDragRequestTime = new Date();
    window.clearTimeout(self.roiDragRequestTimeout);
    self.roiDragRequestTimeout = null;
    self.roiDragRequestTimeoutFcn = null;

    let new_lower_energy = lowerEdgeDrag ? energy : roi.lowerEnergy;
    let new_upper_energy = lowerEdgeDrag ? roi.upperEnergy : energy;
    let new_lower_px = lowerEdgeDrag ? xcenter : self.xScale(roi.lowerEnergy);
    let new_upper_px = lowerEdgeDrag ? self.xScale(roi.upperEnergy) : xcenter;
    
    self.WtEmit(self.chart.id, {name: 'roiDrag'}, new_lower_energy, new_upper_energy, new_lower_px, new_upper_px, roi.lowerEnergy, false );
  };

  let timenow = new Date();
  if( self.roiDragRequestTime === null || (timenow-self.roiDragRequestTime) > 500 ){
    emitFcn();
  } else {
    let dt = Math.min( 500, Math.max(0, 500 - (timenow - self.roiDragRequestTime)) );
    window.clearTimeout( self.roiDragRequestTimeout );
    self.roiDragRequestTimeoutFcn = emitFcn;
    self.roiDragRequestTimeout = window.setTimeout( function(){ 
      if(self.roiDragRequestTimeoutFcn) 
        self.roiDragRequestTimeoutFcn();
    }, dt );
  }

};//SpectrumChartD3.prototype.handleRoiDrag = ...



SpectrumChartD3.prototype.handleStartDragRoi = function(){
  //console.log( 'In handleStartDragRoi()');

  let self = this;
  if( !self.roiDragLine )
    return;

  var m = d3.mouse(self.vis[0][0]);

  d3.select('body').style("cursor", "ew-resize");
  self.roiIsBeingDragged = true;
  var energy = self.xScale.invert(m[0]);
  //var counts = self.self.yScale.invert(m[1]);
  var lpx = self.xScale(self.roiBeingDragged.roi.lowerEnergy);
  var upx = self.xScale(self.roiBeingDragged.roi.upperEnergy);
  var isOnLower = Math.abs(lpx-m[0]) < 5;
  var isOnUpper = Math.abs(upx-m[0]) < 5;
  if( !isOnLower && !isOnUpper ){
    console.log( 'not on ROI edge when down? lpx=' + lpx + ", m[0]=" + m[0] );
    return;
  }
  
  let roiinfo = self.roiBeingDragged;
  var roiPx = (isOnLower ? lpx : upx);
  self.roiDragMouseDown = [m[0], roiPx, energy, isOnLower];
  //console.log( 'self.roiDragMouseDown ', self.roiDragMouseDown );
  
  let y1 = 0;
  let y2 = self.size.height
  
  if( roiinfo && roiinfo.yRangePx && roiinfo.yRangePx.length==2 ){
    y1 = Math.max(0,roiinfo.yRangePx[0]-10);
    y2 = Math.min(y2,roiinfo.yRangePx[1]+10);
  }
  
  var dPx =  m[0] - roiPx;
  //self.roiDragBox
  //    .attr("x", m[0] - dPx - 5)
  //    .attr("y", -10 + y1 + 0.5*(y2-y1));;
  self.roiDragBox.attr("transform", "translate(" + (m[0] - dPx - 5.5) + "," + (-10 + y1 + 0.5*(y2-y1)) + ")");

  self.roiDragLine.attr("x1", roiPx - 0.5)
      .attr("x2", roiPx - 0.5)
      .attr("y1", y1)
      .attr("y2", y2);

  self.roiDragBox.attr("class", "roiDragBox active");
  self.roiDragLine.attr("class", "roiDragLine active");
};//


SpectrumChartD3.prototype.handleCancelRoiDrag = function(){
  let self = this;
  if( !self.roiDragBox && !self.fittingPeak )
    return;
  if( self.roiDragBox )
    self.roiDragBox.remove();
  self.roiDragBox = null;
  if( self.roiDragLine )
    self.roiDragLine.remove();
  self.roiDragLine = null;
  self.roiBeingDragged = null;
  self.roiDragLastCoord = null;
  self.roiDragRequestTime = null;
  self.roiBeingDrugUpdate = null;
  self.roiIsBeingDragged = false;
  self.fittingPeak = null;
  //self.forcedFitRoiNumPeaks = -1;
  window.clearTimeout(self.roiDragRequestTimeout);
  self.roiDragRequestTimeout = null;
  self.roiDragRequestTimeoutFcn = null;
};


SpectrumChartD3.prototype.handleMouseUpDraggingRoi = function(){
  let self = this;
  if( !self.roiIsBeingDragged )
    return;

  console.log( 'Will finish dragging ROI.' );

  let roi = self.roiBeingDragged.roi;
  let m = d3.mouse(self.vis[0][0]);
  let x = m[0], y = m[1];

  let mdx = self.roiDragMouseDown; // [m[0], roiPx, energy, isLowerEdge];
  let xcenter = x + mdx[1] - mdx[0];
  let energy = self.xScale.invert(xcenter);
  //let counts = self.self.yScale.invert(y);

  let lowerEdgeDrag = mdx[3];
  let new_lower_energy = lowerEdgeDrag ? energy : roi.lowerEnergy;
  let new_upper_energy = lowerEdgeDrag ? roi.upperEnergy : energy;
  let new_lower_px = lowerEdgeDrag ? xcenter : self.xScale(roi.lowerEnergy);
  let new_upper_px = lowerEdgeDrag ? self.xScale(roi.upperEnergy) : xcenter;

  self.WtEmit(self.chart.id, {name: 'roiDrag'}, new_lower_energy, new_upper_energy, new_lower_px, new_upper_px, roi.lowerEnergy, true );

  self.handleCancelRoiDrag();
  d3.select('body').style("cursor", "default");
};//SpectrumChartD3.prototype.handleMouseUpDraggingRoi


/* This only updates the temporary ROI.  When you want changes to become final
   you need to call setSpectrumData(...) - this could maybe get changed because
   it is very inefficient
*/
SpectrumChartD3.prototype.updateRoiBeingDragged = function( newroi ){
  let self = this;
  
  if( !self.roiIsBeingDragged && !self.fittingPeak )
    return;

  window.clearTimeout(self.roiDragRequestTimeout);
  self.roiDragRequestTimeout = null;
  if( self.roiDragRequestTimeoutFcn ){
    self.roiDragRequestTimeoutFcn();
    self.roiDragRequestTimeoutFcn = null;
  }

  self.roiDragRequestTime = null;

  self.roiBeingDrugUpdate = newroi;
  self.redraw()();
  self.updateFeatureMarkers(-1);
};


SpectrumChartD3.prototype.handleChartMouseLeave = function() {
  var self = this;

  return function () {
      if (!d3.event)
        return;

      if (!d3.select(d3.event.toElement)[0].parentNode || d3.event.toElement === document.body || d3.event.toElement.nodeName === "HTML" 
              || d3.event.toElement.nodeName === "DIV" || d3.event.toElement.offsetParent === document.body) {

        /* For debugging where the mouse is specifically out of */
        /* if (!d3.select(d3.event.toElement)[0].parentNode) */
        /*   console.log("mouse out of the window"); */
        /* else */
        /*   console.log("mouse out of the chart"); */

        /* Cancel erasing peaks */
        self.handleCancelMouseDeletePeak();

        /* Cancel the right-click-drag action */
        self.handleCancelMouseRecalibration();

        /* Cancel the left-click-drag zoom action */
        self.handleCancelMouseZoomInX();

        /* Cancel the left-click-drag zooming in y axis action */
        self.handleCancelMouseZoomInY();

        /* Cancel count gammas */
        self.handleCancelMouseCountGammas();

        self.handleMouseUpDraggingRoi();
      }

      self.updateFeatureMarkers(-1);

      self.mousedOverRefLine = null;
      self.refLineInfo.style("display", "none");
      self.mouseInfo.style("display", "none");
  }
}

SpectrumChartD3.prototype.handleChartMouseUp = function() {
  var self = this;

  return function () {
    self.xaxisdown = null;
    self.yaxisdown = Math.NaN;
    d3.select(document.body).style("cursor", "default");

    /* Here we can decide to either zoom-in or not after we let go of the left-mouse button from zooming in on the CHART.
       In this case, we are deciding to zoom-in if the above event occurs.

       If you want to do the opposite action, you call self.handleCancelMouseZoomInX()
     */

    self.handleMouseUpDeletePeak();

    self.handleMouseUpZoomInX();

    self.handleMouseUpDraggingRoi();

    self.handleMouseUpZoomInY();

    self.handleMouseUpRecalibration();

    self.handleMouseUpCountGammas();

    self.handleMouseUpDraggingRoi();

    self.lastMouseMovePos = null;
    self.sliderChartMouse = null;
  }
}

SpectrumChartD3.prototype.handleChartWheel = function () {
  var self = this;

  return function() {
    /* Keep event from bubbling up any further */
    if (d3.event) {
      d3.event.preventDefault();
      d3.event.stopPropagation();
    } else
      return;

    /*Get mouse pixel x and y location */
    var m = d3.mouse(self.vis[0][0]);

    /* Handle y axis zooming if wheeling in y-axis */
    if (m[0] < 0 && m[1] > 0 && m[0] < self.size.height && self.options.wheelScrollYAxis) {
      self.handleYAxisWheel();
      return;
    }
  }
}

SpectrumChartD3.prototype.handleChartTouchStart = function() {
  var self = this;

  return function() {
    d3.event.preventDefault();
    d3.event.stopPropagation();
  }
}

SpectrumChartD3.prototype.handleChartTouchEnd = function() {
  var self = this;

  return function() {
    d3.event.preventDefault();
    d3.event.stopPropagation();

    self.sliderBoxDown = false;
    self.leftDragRegionDown = false;
    self.rightDragRegionDown = false;
    self.sliderChartTouch = null;
    self.savedSliderTouch = null;
  }
}


/**
 * -------------- Vis Event Handlers --------------
 */
SpectrumChartD3.prototype.handleVisMouseDown = function () {
  var self = this;

  return function () {
    //console.log("mousedown on plot function!");
    self.dragging_plot = true;

    self.updateFeatureMarkers(null);

    self.mousedowntime = new Date();
    self.mousedownpos = d3.mouse(document.body);

    registerKeyboardHandler(self.keydown());

    if( self.xaxisdown || !isNaN(self.yaxisdown) || self.legdown )
    {
      console.log( "Is null down" )
      return;
    }

    /* Cancel the default d3 event properties */
    d3.event.preventDefault();
    d3.event.stopPropagation(); 

    var m = d3.mouse(self.vis[0][0]);

    if (d3.event.metaKey)
      self.zoomInYMouse = m;
    else
      self.zoomInYMouse = null;

    self.leftMouseDown = null;
    self.zoominmouse = self.deletePeaksMouse = self.countGammasMouse = self.recalibrationMousePos = null; 

    /*
      On Firefox, clicking while holding the Ctrl key triggers a "right click".
      To fix this problem, we save the condition for d3.event.buttons to keep consistent for Firefox/Chrome browsers.
      The d3.event.button condition is saved for other browsers, including Safari.
    */
    if( (d3.event.buttons === 1 || d3.event.button === 0) && m[0] >= 0 && m[0] < self.size.width && m[1] >= 0 && m[1] < self.size.height ) {    /* if left click-and-drag and mouse is in bounds */
      //console.log("left mousedown");

      /* Initially set the escape key flag false */
      self.escapeKeyPressed = false;

      /* Set cursor to move icon */
      d3.select('body').style("cursor", "move");

      /* Set the zoom in/erase mouse properties */
      self.leftMouseDown = self.zoominmouse = self.deletePeaksMouse = self.countGammasMouse = self.recalibrationMousePos = m;
      self.peakFitMouseDown = m;
      self.origdomain = self.xScale.domain();
      self.zoominaltereddomain = false;
      self.zoominx0 = self.xScale.invert(m[0]);

      self.recalibrationStartEnergy = [ self.xScale.invert(m[0]), self.xScale.invert(m[1]) ];
      self.isRecalibrating = false;

      /* We are fitting peaks (if alt-key held) */
      self.fittingPeak = d3.event.ctrlKey && !d3.event.altKey && !d3.event.metaKey && !d3.event.shiftKey && d3.event.keyCode !== 27;
      //self.forcedFitRoiNumPeaks = -1;

      if( self.roiDragLine ){
        self.handleStartDragRoi();
      }else{
        /* Create the initial zoom box if we are not fitting peaks */
        if( !self.fittingPeak && !self.roiIsBeingDragged ) {
          var zoomInXBox = self.vis.select("#zoomInXBox")
              zoomInXText = self.vis.select("#zoomInXText");

          zoomInXBox.remove();
          zoomInXText.remove();

          /* Set the zoom-in box and display onto chart */
          zoomInXBox = self.vis.append("rect")
            .attr("id", "zoomInXBox")
            .attr("class","leftbuttonzoombox")
            .attr("width", 1 )
            .attr("height", self.size.height)
            .attr("x", m[0])
            .attr("y", 0)
            .attr("pointer-events", "none");
        }

        self.updateFeatureMarkers(-1);
      
        self.zooming_plot = true;
      }
      return false;

    } else if ( d3.event.button === 2 ) {    /* listen to right-click mouse down event */
      //console.log("Right mouse down!");
      //console.log(d3.event);
      self.rightClickDown = d3.mouse(document.body);
      self.rightClickDrag = false;
      self.origdomain = self.xScale.domain();

      /* Since this is the right-mouse button, we are not zooming in */
      self.zooming_plot = false;
    } else{

      console.log("Something else: d3.event.buttons=" + d3.event.buttons + ", d3.event.buttom=" + d3.event.button + ", m[0]=" + m[0] + ", self.size.width=" + self.size.width + ", m[1]=" + m[1] + ", self.size.height=" + self.size.height );
    }
  }
}

SpectrumChartD3.prototype.handleVisMouseUp = function () {
  var self = this;

  return function () {
    //console.log("mouseup on vis!");

    if (!d3.event)
      return;

    /* Set the client/page coordinates of the mouse */
    var m = d3.mouse(self.vis[0][0])
        x = m[0],
        y = m[1],
        pageX = d3.event.pageX,
        pageY = d3.event.pageY,
        energy = self.xScale.invert(x),
        count = self.yScale.invert(y);

    /* Handle any of default mouseup actions */
    self.mouseup()();

    /* We are not dragging the plot anymore */
    self.dragging_plot = false;

    /* Update feature marker positions */
    self.updateFeatureMarkers(null);

    /* If the slider chart is displayed and the user clicks on that, cancel the mouse click action */
    if (y >= (self.size.height + 
      (self.xaxistitle != null && !d3.select(self.xaxistitle).empty() ? self.xaxistitle[0][0].clientHeight + 20 : 20) + 
      self.padding.sliderChart)) {
      return;
    }

    /* Figure out right clicks */
    if (d3.event.button === 2 && !self.rightClickDrag && !d3.event.ctrlKey) {
      if( self.highlightedPeak ){
        console.log("Should alter context menu for the highlighted peak" );  
      }
      console.log("Emit RIGHT CLICK (ON PLOT) signal!\nenergy = ", energy, ", count = ", count, ", pageX = ", pageX, ", pageY = ", pageY );
      self.WtEmit(self.chart.id, {name: 'rightclicked'}, energy, count, pageX, pageY);
      return;
    }
    
    /* Figure out clicks and double clicks */
    var nowtime = new Date();
    var clickDelay = 500;

    if (self.mousedownpos && self.dist(self.mousedownpos, d3.mouse(document.body)) < 5) {    /* user clicked on screen */
      if( nowtime - self.mousedowntime < clickDelay ) {

        if (self.lastClickEvent && nowtime - self.lastClickEvent < clickDelay) {    /* check for double click */
          if (self.mousewait) {
            window.clearTimeout(self.mousewait);
            self.mousewait = null;
          }
          console.log("Emit DOUBLE CLICK signal!", "\nenergy = ", energy, ", count = ", count, ", x = ", x, ", y = ", y);
          self.WtEmit(self.chart.id, {name: 'doubleclicked'}, energy, count);

        } else {
          self.mousewait = window.setTimeout((function(e) {
            self.updateFeatureMarkers(self.xScale.invert( x ));    /* update the sum peak where user clicked */

            return function() {
              console.log( "Emit CLICK signal!", "\nenergy = ", energy, ", count = ", count, ", pageX = ", pageX, ", pageY = ", pageY );
              self.WtEmit(self.chart.id, {name: 'leftclicked'}, energy, count, pageX, pageY);

              self.unhighlightPeak(null);
              self.mousewait = null;
            }
          })(d3.event), clickDelay);
        }
        self.lastClickEvent = new Date();
      }
    }

    if( self.xaxisdown || !isNaN(self.yaxisdown) || self.legdown )
      return;

    /* Handle fitting peaks (if needed) */
    if (self.fittingPeak)
      self.handleMouseUpPeakFit();

    /* Handle zooming in x-axis (if needed) */
    self.handleMouseUpZoomInX();

    /* Handle altering ROI mouse up. */
    self.handleMouseUpDraggingRoi();

    /* Handle deleting peaks (if needed) */
    self.handleMouseUpDeletePeak();
    
    /* Handle recalibration (if needed) */
    self.handleMouseUpRecalibration();

    /* Handle zooming in y-axis (if needed) */
    self.handleMouseUpZoomInY();

    /* HAndle counting gammas (if needed) */
    self.handleMouseUpCountGammas();

    self.endYAxisScalingAction()();
    
    let domain = self.xScale.domain();
    if( !self.origdomain || !domain || self.origdomain[0]!==domain[0] || self.origdomain[1]!==domain[1] ){
      //console.log( 'Mouseup xrangechanged' );
      self.WtEmit(self.chart.id, {name: 'xrangechanged'}, domain[0], domain[1], self.size.width, self.size.height );
    }

    /* Delete any other mouse actions going on */
    self.leftMouseDown = null;
    self.zoominbox = null;
    self.zoominx0 = null;
    self.zoominmouse = null;
    self.fittingPeak = null;
    self.escapeKeyPressed = false;
    self.origdomain = null;

    /* Set delete peaks mode off */
    self.isDeletingPeaks = false;
    self.deletePeaksMouse = null;

    /* Set the count gammas mode off */
    self.countGammasMouse = null;

    /* Set the recalibration mode off */
    self.recalibrationMousePos = null;

    self.handleCancelMouseZoomInY();

    /* Set the right click drag and mouse down off */
    self.rightClickDown = null;
    self.rightClickDrag = false;

    /* Cancel default d3 event properties */
    d3.event.preventDefault();
    d3.event.stopPropagation();

    /* Not zooming in anymore */
    self.zooming_plot = false;

    /* Not using x-axis slider anymore */
    self.sliderBoxDown = false;
    self.leftDragRegionDown = false;
    self.rightDragRegionDown = false;
    self.sliderChartMouse = null;
    self.savedSliderMouse = null;
  }
}

SpectrumChartD3.prototype.handleVisWheel = function () {
  var self = this;

  return function () {
    var e = d3.event;

    /*Keep event from bubbling up any further */
    e.preventDefault();
    e.stopPropagation();

    /*If the user is doing anything else, return */
    /*Note that if you do a two finger pinch on a mac book pro, you get e.ctrlKey==true and e.composed==true  */
    if( !e || e.altKey || (e.ctrlKey && !e.composed) || e.shiftKey || e.metaKey || e.button != 0 /*|| e.buttons != 0*/ ) {
     console.log( "Special condition with wheel, ignoring mousewheel e=" + e + ", e.altKey="
                  + e.altKey + ", e.ctrlKey=" + e.ctrlKey + ", e.shiftKey=" + e.shiftKey
                  + ", e.metaKey=" + e.metaKey + ", e.button=" + e.button + ", e.buttons=" + e.buttons );
     return;
    }

    /*Get mouse pixel x and y location */
    var m = d3.mouse(self.vis[0][0]);

    /*Make sure within chart area */
    if( m[0] < 0 || m[0] > self.size.width || m[1] < 0 || m[1] > self.size.height ){

      /* If wheeling in y-axis labels, zoom in the y-axis range */
      if (m[0] < 0 && m[1] > 0 && m[1] < self.size.height && self.options.wheelScrollYAxis && self.rawData && self.rawData.spectra && self.rawData.spectra.length) {
        self.handleYAxisWheel();
        return;
      }

      console.log( "Scroll outside of vis, ignoring mousewheel" );
      return;
    }  

    /*If we are doing any other actions with the chart, then to bad. */
    if( self.dragging_plot || self.zoominbox || self.fittingPeak ){
      console.log( "Plot is being dragged, zoomed, or peak fit, ignoring mousewheel" );
      return;
    }

    /*Dont do anything if there is no data */
    if( !self.rawData || !self.rawData.spectra || self.rawData.spectra.length < 1 ){
      console.log( "No data, ignoring mousewheel" );
      return;
    }

    var mindatax, maxdatax, bounds, foreground;
    foreground = self.rawData.spectra[0];
    bounds = self.min_max_x_values();
    mindatax = bounds[0];
    maxdatax = bounds[1];
    let currentdomain = self.xScale.domain();

    /*Function to clear out any variables assigned during scrolling, or finish */
    /*  up any actions that should be done  */
    function wheelcleanup(e){
      //console.log( "mousewheel, stopped" );

      self.wheeltimer = null;
      self.scroll_start_x = null;
      self.scroll_start_y = null;
      self.scroll_start_domain = null;
      self.scroll_start_raw_channel = null;
      self.scroll_total_x = null;
      self.scroll_total_y = null;

      /* This fun doesnt get called until the timer expires, even if user takes finger
         off of touch-pad or mouse wheel.  This maybe introduces a little bit of potential
         to become out of sinc with things, but we're sending the current range no matter
         what, so I think its okay.
      */
      let domain = self.xScale.domain();
      self.WtEmit(self.chart.id, {name: 'xrangechanged'}, domain[0], domain[1], self.size.width, self.size.height);
    };

    //
    if ((currentdomain[0] <= (mindatax+0.00001) && currentdomain[1] >= (maxdatax-0.00001) && e.deltaX > 0)
        || (currentdomain[1] >= (maxdatax-0.00001) && currentdomain[0] <= (maxdatax+0.00001) && e.deltaX < 0)) {
      //console.log( 'Skipping dealing with mouse wheel - outside data range' );

      //If user has scrolled farther than allowed in either direction, cancel scrolling so that
      //  if they start going the other way, it will immediately react (if we didnt cancel
      //  things, they would have to go past the amount of scrolling they have already done
      //  before they would see any effect)
      if( self.wheeltimer ){
        window.clearTimeout(self.wheeltimer);
        wheelcleanup();
      }

      return;
    }

    /*Here we will set a timer so that if it is more than 1 second since the */
    /*  last wheel movement, we will consider the wheel event over, and start  */
    /*  fresh. */
    /*  This is just an example, and likely needs changed, or just removed. */
    if( self.wheeltimer ){
      /*This is not the first wheel event of the current user wheel action, */
      /*  lets clear the previous timeout (we'll reset a little below).  */
      window.clearTimeout(self.wheeltimer);
    } else {
      //console.log( 'Starting mousewheel action' );
      /*This is the first wheel event of this user wheel action, lets record */
      /*  initial mouse energy, counts, as well as the initial x-axis range. */
      self.scroll_start_x = self.xScale.invert(m[0]);
      self.scroll_start_y = self.yScale.invert(m[1]);
      self.scroll_start_domain = self.xScale.domain();
      self.scroll_start_raw_channel = d3.bisector(function(d){return d;}).left(foreground.x, self.scroll_start_x);
      self.scroll_start_raw_channel = Math.max(0,self.scroll_start_raw_channel);
      self.scroll_start_raw_channel = Math.min(foreground.x.length-1,self.scroll_start_raw_channel);
      self.scroll_total_x = 0;
      self.scroll_total_y = 0;
      self.handleCancelRoiDrag();
    }

    /*scroll_total_x/y is the total number of scroll units the mouse has done */
    /*  since the user started doing this current mouse wheel. */
    self.scroll_total_x += e.deltaX;
    self.scroll_total_y += e.deltaY;

    var MAX_SCROLL_TOTAL = 1500;

    /*Zoom all the way out by the time we get self.scroll_total_y = +200, */
    /*  or, zoom in to 3 bins by the time self.scroll_total_y = -200; */
    self.scroll_total_y = Math.max( self.scroll_total_y, -MAX_SCROLL_TOTAL );
    self.scroll_total_y = Math.min( self.scroll_total_y, MAX_SCROLL_TOTAL );

    //console.log("wheel on chart {" + self.scroll_total_x + "," + self.scroll_total_y + "}");

    var initial_range_x = self.scroll_start_domain[1] - self.scroll_start_domain[0];
    var terminal_range_x;
    if( self.scroll_total_y > 0 ){
      terminal_range_x = (maxdatax - mindatax);
    } else {
     /*Find the bin one to the left of original mouse, and two to the right  */
     var terminalmin = Math.max(0,self.scroll_start_raw_channel - 1);
     var terminalmax = Math.min(foreground.x.length-1,self.scroll_start_raw_channel + 2);
     terminalmin = foreground.x[terminalmin];
     terminalmax = foreground.x[terminalmax];
     terminal_range_x = terminalmax - terminalmin; 
    }

    var frac_y = Math.abs(self.scroll_total_y) / MAX_SCROLL_TOTAL;
    var new_range = initial_range_x + frac_y * (terminal_range_x - initial_range_x);  

    /*Make it so the mouse is over the same energy as when the wheeling started */
    var vis_mouse_frac = m[0] / self.size.width;  

    var new_x_min = self.scroll_start_x - (vis_mouse_frac * new_range);

    var new_x_max = new_x_min + new_range;


    /*Now translate the chart left and right.  100 x wheel units is one initial  */
    /*  width left or right */
    /*  TODO: should probably make it so that on trackpads at least, there is */
    /*        is some threshold on the x-wheel before (like it has to be  */
    /*        greater than the y-wheel) before the panning is applied; this  */
    /*        would also imply treating the x-wheel using deltas on each event */
    /*        instead of using the cumulative totals like now. */
    var mouse_dx_wheel = Math.min(initial_range_x,new_range) * (self.scroll_total_x / MAX_SCROLL_TOTAL);
    new_x_min += mouse_dx_wheel;
    new_x_max += mouse_dx_wheel;

    if( new_x_min < mindatax ){
     new_x_max += (mindatax - new_x_min);
     new_x_min = mindatax; 
    }

    if( new_x_max > maxdatax ){
     new_x_min = Math.max(mindatax,new_x_min-(new_x_max-maxdatax));
     new_x_max = maxdatax;
    }
   
   /*Set a timeout to call wheelcleanup after a little time of not resieving  */
   /*  any user wheel actions. */
   self.wheeltimer = window.setTimeout( wheelcleanup, 250 );
   
   
    if( Math.abs(new_x_min - currentdomain[0]) < 0.000001 
        && Math.abs(new_x_max - currentdomain[1]) < 0.000001 )
    {
      /* We get here when we are fully zoomed out and e.deltaX==0. */
      //console.log( 'We are fully in/out' );
      return;
    }

    //console.log( 'new_x_min=' + new_x_min + ', currentdomain[0]=' + currentdomain[0] 
    //  + "; new_x_max=" + new_x_max + ", currentdomain[1]=" + currentdomain[1] );

    /*Finally set the new x domain, and redraw the chart (which will take care */
    /*  of setting the y-domain). */
    self.setXAxisRange(new_x_min, new_x_max, false);
    self.redraw()();

    self.updateFeatureMarkers(-1);
  }
}

SpectrumChartD3.prototype.handleVisTouchStart = function() {
  var self = this;

  return function() {

      /* Prevent default event actions from occurring (eg. zooming into page when trying to zoom into graph) */
      d3.event.preventDefault();
      d3.event.stopPropagation();

      /* Get the touches on the screen */
      var t = d3.touches(self.vis[0][0]),
          touchHoldTimeInterval = 600;

      /* Save the original zoom scale and translation */
      self.savedZoomScale = self.zoom.scale();
      self.savedZoomTranslation = self.zoom.translate();

      /* Represent where we initialized our touch start value */
      self.touchStart = t;
      self.touchStartEvent = d3.event;
      self.touchPageStart = d3.touches(document.body).length === 1 ? [d3.event.pageX, d3.event.pageY] : null;

      if (t.length === 2) {
        self.countGammasStartTouches = self.createPeaksStartTouches = self.touchStart;
      }

      self.updateTouchesOnChart(self.touchStartEvent);

      /* Boolean for the touch of a touch-hold signal */
      self.touchHoldEmitted = false;

      self.touchHold = window.setTimeout((function(e) {
        var x = t[0][0],
            y = t[0][1],
            pageX = d3.event.pageX,
            pageY = d3.event.pageY,
            energy = self.xScale.invert(x),
            count = self.yScale.invert(y);

        return function() {

          /* Emit the tap signal, unhighlight any peaks that are highlighted */
            if (self.touchStart && self.touchPageStart && self.dist([pageX, pageY], self.touchPageStart) < 5 && !self.touchHoldEmitted) {
            console.log( "Emit TAP HOLD (RIGHT TAP) signal!", "\nenergy = ", energy, ", count = ", count, ", x = ", x, ", y = ", y );
            self.WtEmit(self.chart.id, {name: 'rightclicked'}, energy, count, pageX, pageY);
            self.unhighlightPeak(null);
            self.touchHoldEmitted = true;
          }

          /* Clear the touch hold wait, the signal has already been emitted */
          self.touchHold = null;
        }     
      })(d3.event), touchHoldTimeInterval);
    }
}

SpectrumChartD3.prototype.handleVisTouchMove = function() {
  var self = this;

  /* Touch interaction helpers */
  function isDeletePeakSwipe() {

    if (!self.touchesOnChart)
      return false;

    var keys = Object.keys(self.touchesOnChart);

    /* Delete peak swipe = two-finger vertical swipe */
    if (keys.length !== 2)
      return false;

    var maxDyDiff = 15,
        minDxDiff = 25;

    var t1 = self.touchesOnChart[keys[0]],
        t2 = self.touchesOnChart[keys[1]];

    var dy1 = t1.startY - t1.pageY,
        dy2 = t2.startY - t2.pageY,
        dyDiff = Math.abs(dy2 - dy1);

    if (dyDiff > maxDyDiff || Math.abs(t1.pageX - t2.pageX) < minDxDiff) {
      return false;
    }

    var dy = Math.min(dy1,dy2),
        dx1 = t1.startX - t1.pageX,
        dx2 = t2.startX - t2.pageX,
        dx = Math.abs(dx1 - dx2);

    return dy > dx && dy > maxDyDiff;
  }

  function isControlDragSwipe() {

    if (!self.touchesOnChart)
      return false;

    var keys = Object.keys(self.touchesOnChart);

    if (keys.length !== 2)
      return false;

    var t1 = self.touchesOnChart[keys[0]],
        t2 = self.touchesOnChart[keys[1]];

    if (t1.startX > t1.pageX || t2.startX > t2.pageX)
      return false;

    if( !isFinite(t1.startX) || !isFinite(t1.pageX)
    || !isFinite(t2.startX) || !isFinite(t2.pageX)
    || !isFinite(t1.startY) || !isFinite(t1.pageY)
    || !isFinite(t2.startY) || !isFinite(t2.pageY) )
      return false;

    var startdx = t1.startX - t2.startX;
        nowdx = t1.pageX - t2.pageX;
        yavrg = 0.5*(t1.startY+t2.startY);

    if( Math.abs(yavrg-t1.pageY) > 20 || 
        Math.abs(yavrg-t2.pageY) > 20 || 
        Math.abs(startdx-nowdx) > 20 ) 
      return false;

    return Math.abs(t1.pageX - t1.startX) > 30;
  }

  function isAltShiftSwipe() {
    var keys = Object.keys(self.touchesOnChart);

    if( keys.length !== 2 ) 
      return false;

    var t1 = self.touchesOnChart[keys[0]],
        t2 = self.touchesOnChart[keys[1]];

    if( Math.abs(t1.startX-t2.startX) > 20 || Math.abs(t1.pageX-t2.pageX) > 25 )
      return false;

    return ( (t1.pageX - t1.startX) > 30 );
  }

  function isZoomInYPinch() {
    if (!self.touchesOnChart)
      return false;

    var keys = Object.keys(self.touchesOnChart);

    if (keys.length !== 2)
      return false;

    var touch1 = self.touchesOnChart[keys[0]];
    var touch2 = self.touchesOnChart[keys[1]];
    var adx1 = Math.abs( touch1.startX - touch2.startX );
    var adx2 = Math.abs( touch1.pageX  - touch2.pageX );
    var ady1 = Math.abs( touch1.startY - touch2.startY );
    var ady2 = Math.abs( touch1.pageY  - touch2.pageY );
    var ddx = Math.abs( adx2 - adx1 );
    var ddy = Math.abs( ady2 - ady1 );
    var areVertical = (adx2 > ady2);

    return ddx < ddy && ddy>20
  }

  function deleteTouchLine() {
    /* Delete the touch lines if they exist on the vis */

    if (self.touchLineX) {
      self.touchLineX.remove();
      self.touchLineX = null;
    }

    if (self.touchLineY) {
      self.touchLineY.remove();
      self.touchLineY = null;
    }
  }

  return function() {

      /* Prevent default event actions from occurring (eg. zooming into page when trying to zoom into graph) */
      d3.event.preventDefault();
      d3.event.stopPropagation();

      /* Nullify our touchstart position, we are now moving our touches */
      self.touchStart = null;

      /* Get the touches on the chart */
      var t = d3.touches(self.vis[0][0]);

      if (t.length === 2) {
        self.deletePeaksTouches = t;
      }

      /* Panning = one finger drag */
      self.touchPan = t.length === 1;
      self.deletePeakSwipe = isDeletePeakSwipe() && !self.currentlyAdjustingSpectrumScale;
      self.controlDragSwipe = isControlDragSwipe() && !self.currentlyAdjustingSpectrumScale;
      self.altShiftSwipe = isAltShiftSwipe() && !self.currentlyAdjustingSpectrumScale;
      self.zoomInYPinch = isZoomInYPinch() && !self.currentlyAdjustingSpectrumScale;

      if (self.deletePeakSwipe) {
        self.handleTouchMoveDeletePeak();

      } else if (self.controlDragSwipe) {
        self.handleTouchMovePeakFit();

      } else if (self.altShiftSwipe) {
        self.handleTouchMoveCountGammas();

      } else if (self.zoomInYPinch) {
        self.handleTouchMoveZoomInY();

      } else if (self.currentlyAdjustingSpectrumScale) {
        self.handleMouseMoveScaleFactorSlider()();

      } else {
        self.handleCancelTouchCountGammas();
        self.handleCancelTouchDeletePeak();
        self.handleCancelTouchPeakFit();
        self.handleTouchCancelZoomInY();
      }

      /* 
      Clear the touch hold signal if:
        - More than one touches on chart
        - No touch positions on the page detected
        - We moved our touches by > 5 pixels
      */
      if (t.length > 1 || !self.touchPageStart || self.dist([d3.event.pageX, d3.event.pageY], self.touchPageStart) > 5) {
        if (self.touchHold) {
          window.clearTimeout(self.touchHold);
          self.touchHold = null;
        }
      }


      /* Update mouse coordinates, feature markers on a touch pan action */
      if (self.touchPan) {
        self.mousemove();
        self.updateMouseCoordText();
        self.updateFeatureMarkers(-1);
      }

      /* Hide the peak info */
      self.hidePeakInfo();

      /* Delete the touch line */
      deleteTouchLine();

      /* Update our map of touches on the chart */
      self.updateTouchesOnChart(d3.event);

      self.lastTouches = t;
    }
}

SpectrumChartD3.prototype.handleVisTouchEnd = function() {
  var self = this;

  function updateTouchLine(touches) {

    /* Touches is an error, abort function */
    if (!touches)
      return;

    /* Do not update the touch line (remove it) if there are more than two touches on the screen */
    if (touches.length != 1) {
      deleteTouchLine();
      return;
    }

    /* Set the coordinates of the touch */
    var t = touches[0];

    /* Create the x-value touch line, or update its coordinates if it already exists */
    if (!self.touchLineX) {
      self.touchLineX = self.vis.append("line")
        .attr("class", "touchLine")
        .attr("x1", t[0])
        .attr("x2", t[0])
        .attr("y1", 0)
        .attr("y2", self.size.height);

    } else {
      self.touchLineX.attr("x1", t[0])
        .attr("x2", t[0])
    }

    /* Create the y-value touch line, or update its coordinates if it already exists */
    if (!self.touchLineY) {
      self.touchLineY = self.vis.append("line")
        .attr("class", "touchLine")
        .attr("x1", t[0]-10)
        .attr("x2", t[0]+10)
        .attr("y1", t[1])
        .attr("y2", t[1]);
    } else {
      self.touchLineY.attr("x1", t[0]-10)
        .attr("x2", t[0]+10)
        .attr("y1", t[1])
        .attr("y2", t[1]);
    }
  }
  function deleteTouchLine() {

    /* Delete the touch lines if they exist on the vis */
    if (self.touchLineX) {
      self.touchLineX.remove();
      self.touchLineX = null;
    }

    if (self.touchLineY) {
      self.touchLineY.remove();
      self.touchLineY = null;
    }
  }

  return function() {

      /* Prevent default event actions from occurring (eg. zooming into page when trying to zoom into graph) */
      d3.event.preventDefault();
      d3.event.stopPropagation();

      /* Get the touches on the screen */
      var t = d3.event.changedTouches;
      var visTouches = d3.touches(self.vis[0][0]);
      if (visTouches.length === 0) {
        self.touchesOnChart = null;
      }

      if (self.touchPan)
        console.log("touchend from pan!");

      else {
        /* Detect tap/double tap signals */
        if (t.length === 1 && self.touchStart) {

          /* Get page, chart coordinates of event */
          var x = self.touchStart[0][0],
              y = self.touchStart[0][1],
              pageX = d3.event.pageX,
              pageY = d3.event.pageY
              currentTapEvent = d3.event,
              energy = self.xScale.invert(x),
              count = self.yScale.invert(y);

          /* Set the double tap setting parameters */
          var tapRadius = 35,                   /* Radius area for where a double-tap is valid (anything outside this considered a single tap) */
              doubleTapTimeInterval = 500;      /* Time interval for double tap */

          /* Update the feature marker positions (argument added for sum peaks) */
          self.updateFeatureMarkers(self.xScale.invert(x));

          /* Update the touch line position */
          updateTouchLine(self.touchStart);

          /* Emit the proper TAP/DOUBLE-TAP signal */
          if (self.touchPageStart && self.dist(self.touchPageStart, [pageX, pageY]) < tapRadius ) {

            if (self.lastTapEvent &&
                  self.lastTapEvent.timeStamp && currentTapEvent.timeStamp - self.lastTapEvent.timeStamp < doubleTapTimeInterval &&
                  self.dist([self.lastTapEvent.pageX, self.lastTapEvent.pageY], [pageX, pageY]) < tapRadius) {

              /* Clear the single-tap wait if it exists, then emit the double tap signal */
              if (self.tapWait) {
                window.clearTimeout(self.tapWait);
                self.tapWait = null;
              }

              /* Emit the double-tap signal, clear any touch lines/highlighted peaks in chart */
              console.log("Emit DOUBLE TAP signal!", "\nenergy = ", energy, ", count = ", count, ", x = ", x, ", y = ", y);
              self.WtEmit(self.chart.id, {name: 'doubleclicked'}, energy, count);
              deleteTouchLine();
              self.unhighlightPeak(null);
            } else {

              /* Create the single-tap wait emit action in case there is no more taps within double tap time interval */
              self.tapWait = window.setTimeout((function(e) {

                /* Move the feature markers to tapped coordinate */
                self.updateFeatureMarkers(self.xScale.invert(x));    /* update the sum peak where user clicked */

                /* Don't emit the tap signal if there was a tap-hold */
                if (self.touchHoldEmitted)
                  return false;

                return function() {

                  /* Emit the tap signal, unhighlight any peaks that are highlighted */
                  console.log( "Emit TAP signal!", "\nx = ", x, ", y = ", y, ", pageX = ", pageX, ", pageY = ", pageY );
                  self.unhighlightPeak(null);
                  var touchStartPosition = self.touchStart;

                  /* Highlight peaks where tap position falls */
                  if (self.peakPaths) {
                    const xen = self.xScale.invert(x);
                    for (i = self.peakPaths.length-1; i >= 0; i--) {
                      if (xen >= self.peakPaths[i].lowerEnergy && xen <= self.peakPaths[i].upperEnergy) {
                        const path = self.peakPaths[i].path;
                        const paths = self.peakPaths[i].paths;
                        const roi = self.peakPaths[i].roi;
                        self.handleMouseOverPeak(path);
                        break;
                      }
                    }
                  }
                  /* Clear the single-tap wait, the signal has already been emitted */
                  self.tapWait = null;
                }     
              })(d3.event), doubleTapTimeInterval);
            
            }

            /* Set last tap event to current one */
            self.lastTapEvent = currentTapEvent;
          }

        } else    /* Touch move detected, aborting tap signal */
          self.updateFeatureMarkers(-1);
      }

      self.updateTouchesOnChart(d3.event);
      self.updateMouseCoordText();
      self.updatePeakInfo();

      self.handleTouchEndCountGammas();
      self.handleTouchEndDeletePeak();
      self.handleTouchEndPeakFit();
      self.handleTouchEndZoomInY();
      

      self.touchPan = false;
      self.touchZoom = false;
      self.touchStart = null;
      self.touchStart = null;
      self.touchHoldEmitted = false;

      self.deletePeakSwipe = false;
      self.controlDragSwipe = false;
      self.altShiftSwipe = false;
      self.zoomInYPinch = false;

      self.countGammasStartTouches = null;

      self.sliderBoxDown = false;
      self.leftDragRegionDown = false;
      self.rightDragRegionDown = false;
      self.sliderChartTouch = null;
      self.savedSliderTouch = null;
    };
}


/**
 * -------------- General Key/Mouse Event Handlers --------------
 */
SpectrumChartD3.prototype.mousemove = function () {
  var self = this;

  return function() {
    /*This function is called whenever a mouse movement occurs */
    /* console.log("mousemove function called from ", d3.event.type); */

    var p = d3.mouse(self.vis[0][0]),
        t = d3.event.changedTouches;

    var energy = self.xScale.invert(p[0]),
        mousey = self.yScale.invert(p[1]);


    self.updateFeatureMarkers(-1);
    self.updateMouseCoordText();
    self.updatePeakInfo();

    if( self.legdown ) {
      d3.event.preventDefault();
      d3.event.stopPropagation();

      var x = d3.event.x ? d3.event.x : d3.event.touches ?  d3.event.touches[0].clientX : d3.event.clientX,
          y = d3.event.y ? d3.event.y : d3.event.touches ?  d3.event.touches[0].clientY : d3.event.clientY,
          calculated_x = d3.mouse(self.vis[0][0])[0]; /* current mouse x position */

      if ( calculated_x >= -self.padding.leftComputed && y >= 0 && 
           calculated_x <= self.cx && y <= self.cy ) {
        /* console.log("change legend pos"); */
        var tx = (x - self.legdown.x) + self.legdown.x0;
        var ty = (y - self.legdown.y) + self.legdown.y0; 
        self.legend.attr("transform", "translate(" + tx + "," + ty + ")");
      }
    }

    if (self.adjustingBackgroundScale || self.adjustingSecondaryScale) {
      d3.event.preventDefault();
      d3.event.stopPropagation();
    }

    if( self.rawData && self.rawData.spectra && self.rawData.spectra.length ) {
      var foreground = self.rawData.spectra[0];
      var lowerchanval = d3.bisector(function(d){return d.x;}).left(foreground.points,energy,1) - 1;
      var counts = foreground.points[lowerchanval].y;
      var lefteenergy = foreground.points[lowerchanval].x;
      var rightenergy = foreground.points[lowerchanval+1>=foreground.points.length ? foreground.points.length-1 : lowerchanval+1].x;
      var midenergy = 0.5*(lefteenergy + rightenergy);
      var detchannel = lowerchanval*foreground.rebinFactor;

      /*Here is where we would update some sort of display or whatever */
      /*console.log( "counts=" + counts + " in " + self.rebinFactor + " channels, starting at energy " + lefteenergy ); */

      /* self.focus.attr("transform", "translate(" + self.xScale(midenergy) + "," + self.yScale(counts) + ")"); */
      /* self.focus.style("display", null); */
      /* self.focus.select("text").text( "counts=" + counts + " in " + self.rebinFactor + " channels, starting at energy " + lefteenergy ); */

    } else {
      /* self.focus.style("display", "none"); */
    }


    if (self.dragged) {
      /*We make it here if a data point is dragged (which is not allowed) */

      /*self.dragged.y = self.yScale.invert(Math.max(0, Math.min(self.size.height, p[1]))); */
      self.update(false); /* boolean set to false to indicate no animation needed */
    };
    if( self.xaxisdown && self.xScale.invert(p[0]) > 0) {       /* make sure that xaxisDrag does not go lower than 0 (buggy behavior) */
      /* We make it here when a x-axis is clicked on, and has been dragged a bit */
      d3.select('body').style("cursor", "ew-resize");
      
      let newenergy = self.xScale.invert(p[0]);
      
      if ( self.rawData && self.rawData.spectra && self.rawData.spectra.length ) {
        let origxmin = self.xaxisdown[1];
        let origxmax = self.xaxisdown[2];
        let e_width = origxmax - origxmin;
        
        let newEnergyFrac = (newenergy - self.xScale.domain()[0]) / (origxmax - origxmin);
        let newX0 = self.xaxisdown[0] - newEnergyFrac*e_width;
        let newX1 = self.xaxisdown[0] + (1-newEnergyFrac)*e_width;
 
        let lowerData = self.rawData.spectra[0].x[0];
        let upperData = self.rawData.spectra[0].x[self.rawData.spectra[0].x.length-1];
       
        if( newX0 < lowerData ){
          newX1 = Math.min( upperData, newX1 + (lowerData - newX0) );
          newX0 = lowerData;
        }
       
        if( newX1 > upperData ){
          newX0 = Math.max( lowerData, newX0 - (newX1 - upperData) );
          newX1 = upperData;
        }
       
        //we'll emit on mouse up - ToDo: set a timer to periodically emit 'xrangechanged' while dragging.
        self.setXAxisRange(newX0, newX1, false);
        self.redraw()();
      }

      d3.event.preventDefault();
      d3.event.stopPropagation();
    };

    if (!isNaN(self.yaxisdown)) {
      let olddomain = self.getYAxisDomain();
      let old_ymax = olddomain[0];
      let old_ymin = olddomain[1];
      
      d3.select('body').style("cursor", "ns-resize");
      var rupy = self.yScale.invert(p[1]),
          yaxis1 = self.yScale.domain()[1],
          yaxis2 = self.yScale.domain()[0],
          yextent = yaxis2 - yaxis1;
          
      if (rupy > 0) {
        var changey, new_domain;
        changey = self.yaxisdown / rupy;

        new_domain = [yaxis1 + (yextent * changey), yaxis1];
        
        let ydatarange = self.getYAxisDataDomain();
        let newYmin = new_domain[1];
        let newYmax = new_domain[0];
        let y0 = ydatarange[0];
        let y1 = ydatarange[1];
        
        if( self.options.yscale == "log" ) {
          if( newYmin > 0 && newYmax > newYmin && y1 > 0 ){
            let logY0 = ((y0<=0) ? -1 : Math.log10(y0));
            let logY1 = ((y1<=0) ? 0 : Math.log10(y1));
          
            let newLogLowerY = Math.log10(newYmin);
            let newLogUpperY = Math.log10(newYmax);
            
            if( newLogUpperY < logY1 ) {
              self.options.logYFracTop = 0;  //make sure we can at least see the whole chart.
            } else {
              let newfrac = (newLogUpperY - logY1) / (logY1 - logY0);
              if( !isNaN(newfrac) && isFinite(newfrac) && newfrac>=0 && newfrac<50 ){
                self.options.logYFracTop = (newLogUpperY - logY1) / (logY1 - logY0);
                //Should emit something noting we changed something
              }
            }
            
            //Dragging on the y-axis only adjusts the top fraction, not the bottom, so we wont set the bottom here (since it shouldnt change)
            //self.options.logYFracBottom should be between about 0 and 10
            //self.options.logYFracBottom = (logY1 - logY0) / (newYmin - logY0);
          }//if( new limits are reasonable )
        } else if( self.options.yscale == "lin" ) {
          let newfrac = (newYmax / y1) - 1.0;
          
          console.log( 'newfrac=' + newfrac );
          if( !isNaN(newfrac) && isFinite(newfrac) && newfrac>=0 && newfrac<50 ){
            self.options.linYFracTop = newfrac;
          }
        } else if( self.options.yscale == "sqrt" ) {
          //self.options.sqrtYFracBottom = 1 - (newYmin / y0);  //Shouldnt change though
          self.options.sqrtYFracTop = -1 + (newYmax / y1);
        }
      
        
        self.yScale.domain(new_domain);
        self.redraw()();
      }

      d3.event.preventDefault();
      d3.event.stopPropagation();
    }
  }
}

SpectrumChartD3.prototype.mouseup = function () {
  var self = this;
  return function() {
    document.onselectstart = function() { return true; };
    d3.select('body').style("cursor", "auto");
    d3.select('body').style("cursor", "auto");
    if( self.xaxisdown ) {
      self.redraw()();
      self.xaxisdown = null;

      /*d3.event.preventDefault(); */
      /*d3.event.stopPropagation(); */
    };
    if (!isNaN(self.yaxisdown)) {
      self.redraw()();
      self.yaxisdown = Math.NaN;
      /*d3.event.preventDefault(); */
      /*d3.event.stopPropagation(); */
    }
    if (self.dragged) {
      self.dragged = null
    }

    self.sliderBoxDown = false;
    self.leftDragRegionDown = false;
    self.rightDragRegionDown = false;
    self.sliderChartMouse = null;
    self.savedSliderMouse = null;
    self.currentlyAdjustingSpectrumScale = null;
  }
}

SpectrumChartD3.prototype.keydown = function () {
  var self = this;
  return function() {

    /*if (!self.selected) return; */

    if( self.roiDragBox && (d3.event.ctrlKey || d3.event.altKey || d3.event.metaKey || d3.event.shiftKey) ){
      let needredraw = self.roiBeingDragged;
      self.handleCancelRoiDrag();
      d3.select('body').style("cursor", "default");
      if( needredraw )
        self.redraw()();
    }
    
    
    switch (d3.event.keyCode) {
      case 27: { /*escape */
        self.escapeKeyPressed = true;
        self.cancelYAxisScalingAction();
        self.handleCancelAllMouseEvents()();
        self.handleCancelAnimationZoom();
        self.handleCancelRoiDrag();
        self.redraw()();
      }
      
      case 8: /* backspace */
      case 46: { /* delete */
        break;
      }
    }
    
    /* if the user is cntl/alt-dragging a ROI, they can force the number of peaks
     they would like in it by hitting the 1 through 9 keys.
     A value of self.forcedFitRoiNumPeaks equal or less (default) than zero means the fitting code should decide how many peaks
     (currently not enforcing
     */
    //if( self.fittingPeak && d3.event.keyCode >= 49 && d3.event.keyCode <= 57 ){
    //  self.forcedFitRoiNumPeaks = d3.event.keyCode - 48;
    //  const roi = self.roiBeingDrugUpdate;
    //  if( roi ){
    //    window.clearTimeout(self.roiDragRequestTimeout);
    //    self.WtEmit(self.chart.id, {name: 'fitRoiDrag'}, roi.lowerEnergy, roi.upperEnergy, self.forcedFitRoiNumPeaks, false, d3.event.pageX, d3.event.pageY );
    //  }
    //}
  }
}

SpectrumChartD3.prototype.updateTouchesOnChart = function (touchEvent) {
  var self = this;

  /* Don't do anything if touch event not recognized */
  if (!touchEvent || !touchEvent.type.startsWith("touch"))
    return false;

  /* Create dictionary of touches on the chart */
  if (!self.touchesOnChart)
    self.touchesOnChart = {};

  /* Add each touch start into map of touches on the chart */
  var touch;
  for (i = 0; i < touchEvent.touches.length; i++) {
    /* Get the touch  */
    touch = touchEvent.touches[i];

    /* Here we add a new attribute to each touch: the start coordinates of the touch */
    /*   If the touch already exists in our map, then just update the start coordinates of the new touch */
    touch.startX = self.touchesOnChart[touch.identifier] ? self.touchesOnChart[touch.identifier].startX : touch.pageX;
    touch.startY = self.touchesOnChart[touch.identifier] ? self.touchesOnChart[touch.identifier].startY : touch.pageY;

    /* Add/replace touch into dictionary */
    self.touchesOnChart[touch.identifier] = touch;
  }

  /* Delete any touches that are not on the screen anymore (read from 'touchend' event) */
  if (touchEvent.type === "touchend") {
    for (i = 0; i < touchEvent.changedTouches.length; i++) {
      touch = touchEvent.changedTouches[i];

      if (self.touchesOnChart[touch.identifier])
        delete self.touchesOnChart[touch.identifier];
    }
  }
}

SpectrumChartD3.prototype.handleCancelAllMouseEvents = function() {
  var self = this;

  return function () {

    d3.select(document.body).style("cursor", "default");
    self.xaxisdown = null;
    self.yaxisdown = Math.NaN;

    /* Cancel recalibration */
    self.handleCancelMouseRecalibration();

    /* Cancel deleting peaks */
    self.handleCancelMouseDeletePeak();

    /* Cancel zooming in x-axis */
    self.handleCancelMouseZoomInX();

    /* Cancel zooming in y-axis */
    self.handleCancelMouseZoomInY();

    /* Cancel counting gammas */
    self.handleCancelMouseCountGammas();

    /* Cancel peak fitting */
    self.erasePeakFitReferenceLines();

    /* Cancel dragging of ROI. */
    self.handleCancelRoiDrag();
    
    /* Canceling out all mouse events for chart */
    self.zooming_plot = false;
    self.dragging_plot = false;
    self.recalibrationStartEnergy = null;

    /* Cancel all kept mouse positions for mouse events */
    self.leftMouseDown = null;
    self.zoominmouse = self.deletePeaksMouse = self.countGammasMouse = self.recalibrationMousePos = null;
    self.rightClickDown = null;

    /* Cancel all legend interactions */
    self.legdown = null;

    /* Cancel all slider drag region interactions */
    self.sliderBoxDown = false;
    self.leftDragRegionDown = false;
    self.rightDragRegionDown = false;

    /* Cancel all scaler widget interactions */
    self.endYAxisScalingAction()();
  }
}

SpectrumChartD3.prototype.drawSearchRanges = function() {
  var self = this;

  if( !self.searchEnergyWindows || !self.searchEnergyWindows.length ){
    self.vis.selectAll("g.searchRange").remove();
    return;
  }

  let domain = self.xScale.domain();
  let lx = domain[0], ux = domain[1];

  let inrange = [];
  
  self.searchEnergyWindows.forEach( function(w){
    let lw = w.energy - w.window;
    let uw = w.energy + w.window;

    if( (uw > lx && uw < ux) || (lw > lx && lw < ux) || (lw <= lx && uw >= ux) )
      inrange.push(w);
  } );

  var tx = function(d) { return "translate(" + self.xScale(Math.max(lx,d.energy-d.window)) + ",0)"; };
  var gy = self.vis.selectAll("g.searchRange")
            .data( inrange, function(d){return d.energy;} )
            .attr("transform", tx)
            .attr("stroke-width",1);

  var gye = gy.enter().insert("g", "a")
    .attr("class", "searchRange")
    .attr("transform", tx);

  let h = self.size.height;
  
  gye.append("rect")
    //.attr("class", "d3closebut")
    .attr('y', '0' /*function(d){ return self.options.refLineTopPad;}*/ )
    .attr("x", "0" )
    .style("fill", 'rgba(255, 204, 204, 0.4)')
     ;
     
  var stroke = function(d) { return d.energy>=lx && d.energy<=ux ? '#4C4C4C' : 'rgba(0,0,0,0);'; };

  gye.append("line")
    .attr("y1", h )
    .style("stroke-dasharray","4,8")
     ;

  /* Remove old elements as needed. */
  gy.exit().remove();

  gy.select("rect")
    .attr('height', h /*-self.options.refLineTopPad*/ )
    .attr('width', function(d){ 
      let le = Math.max( lx, d.energy - d.window );
      let ue = Math.min( ux, d.energy + d.window );
      return self.xScale(ue) - self.xScale(le); 
    } );
 
  
  let linepos = function(d){ 
    let le = Math.max( lx, d.energy - d.window );
    return self.xScale(d.energy) - self.xScale(le) /* - 0.5*/; 
  };

  gy.select("line")
    .attr("stroke", stroke )
    .attr("x1", linepos )
    .attr("x2", linepos )
    .attr("y1", h )  //needed for initial load sometimes
    .attr("y2", '0' /*function(d){ return self.options.refLineTopPad; }*/ );
}//drawSearchRanges(...)



SpectrumChartD3.prototype.drawHighlightRegions = function(){
  var self = this;
  
  if( !Array.isArray(self.highlightRegions) || self.highlightRegions.length===0 )
    return;
  
  //highlightRegions is array of form: [{lowerEnergy,upperEnergy,fill,hash}]
 
  if( !self.highlightRegions || !self.highlightRegions.length ){
    self.vis.selectAll("g.highlight").remove();
    return;
  }
 
  let domain = self.xScale.domain();
  let lx = domain[0], ux = domain[1];
 
  let inrange = [];
 
  self.highlightRegions.forEach( function(w){
    let lw = w.lowerEnergy;
    let uw = w.upperEnergy;
   
    if( (uw > lx && uw < ux) || (lw > lx && lw < ux) || (lw <= lx && uw >= ux) )
      inrange.push(w);
  } );
 
  var tx = function(d) { return "translate(" + self.xScale(Math.max(lx,d.lowerEnergy)) + ",0)"; };
  var gy = self.vis.selectAll("g.highlight")
               .data( inrange, function(d){return d;} )
               .attr("transform", tx);
 
  var gye = gy.enter().insert("g", "a")
               .attr("class", "highlight")
               .attr("transform", tx);
 
  let h = self.size.height;
 
  gye.append("rect")
   //.attr("class", "d3closebut")
     .attr('y', '0' /*function(d){ return self.options.refLineTopPad;}*/ )
     .attr("x", "0" )
     .style("fill", function(d){return d.fill;} );
 
  /* Remove old elements as needed. */
  gy.exit().remove();
 
  gy.select("rect")
    .attr('height', h /*-self.options.refLineTopPad*/ )
    .attr('width', function(d){
      let le = Math.max( lx, d.lowerEnergy );
      let ue = Math.min( ux, d.upperEnergy );
      return self.xScale(ue) - self.xScale(le);
 } );
}//drawHighlightRegions(...)


/**
 * -------------- Reference Gamma Lines Functions --------------
 */
SpectrumChartD3.prototype.drawRefGammaLines = function() {
  /*Drawing of the refrenece lines is super duper un-optimized!!! */
  var self = this;

  if( !self.refLines || !self.refLines.length || !self.refLines[0].lines  || !self.refLines[0].lines.length ) {
    /*console.log( "no reference lines, " + self.refLines.length ); */
    self.vis.selectAll("g.ref").remove();
    return;
  }

  function getLinesInRange(xrange,lines) {
    var bisector = d3.bisector(function(d){return d.e;});
    var lindex = bisector.left( lines, xrange[0] );
    var rindex = bisector.right( lines, xrange[1] );
    return lines.slice(lindex,rindex).filter(function(d){return d.h > 1E-16;});
  }

  var lowerx = this.xScale.domain()[0], upperx = this.xScale.domain()[1];


  var reflines = [];
  self.refLines.forEach( function(input) {
    var lines = getLinesInRange(self.xScale.domain(),input.lines);
    input.maxVisibleAmp = d3.max(lines, function(d){return d.h;});  /*same as lines[0].parent.maxVisibleAmp = ... */
    reflines = reflines.concat( lines );
  });

  reflines.sort( function(l,r){ return ((l.e < r.e) ? -1 : (l.e===r.e ? 0 : 1)); } );

  var tx = function(d) { return "translate(" + self.xScale(d.e) + ",0)"; };
  var gy = self.vis.selectAll("g.ref")
            .data( reflines, function(d){return d.id;} )
            .attr("transform", tx)
            .attr("stroke-width",1);

  var gye = gy.enter().insert("g", "a")
    .attr("class", "ref")
    .attr("transform", tx);

  /*color:'#0000FF',parent:'Ba133',age:'0.00 us',lines:[{e:30.27,h:6.22e-05,pa */
  var stroke = function(d) { return d.parent.color; };

  var dashfunc = function(d){
    var particles = ["gamma", "xray", "beta", "alpha",   "positron", "electronCapture"];
    var dash      = [null,    ("3,3"),("1,1"),("3,2,1"), ("3,1"),    ("6,6") ];
    var index = particles.indexOf(d.particle);
    if( index < 0 ) { console.log( 'Invalid particle: ' + d.particle ); return null; }
    return (index > -1) ? dash[index] : null;
  };

  var h = self.size.height;
  var m = Math.min(h,self.options.refLineTopPad); /*leave 20px margin at top of chart */


  gye.append("line")
    .style("stroke-dasharray", dashfunc )
    .attr("stroke", stroke )
    /* .attr("class", function(d,i){ return "refline " + i;} ) */
    .attr("y1", h )
    .attr("dx", "-0.5" )
    /* .attr("y2", function(d){ console.log("y2="); return h - (h-m)*d.h/maxVisibleAmp; } ) */
    /*.on("mouseover", function(d) { d3.select(this).style("stroke-width", "3");}) */
    /*.on("mouseout",  function(d) { d3.select(this).style("stroke-width", "1");}) */
     ;

  /* EXIT */
  /* Remove old elements as needed. */
  gy.exit().remove();

  /*Now update the height of all the lines.  If we did this in the gye.append("line") */
  /*  line above then the values for existing lines wouldnt be updated (only */
  /*  the new lines would have correct height) */
  gy.select("line")
    .attr("y2", function(d){ return Math.min(h - (h-m)*d.h/d.parent.maxVisibleAmp,h-2) ; } )
    .attr("y1", h );  //needed for initial load sometimes
}

SpectrumChartD3.prototype.refreshRefGammaLines = function() {
  var self = this;

  // No need to clear, we don't have any data
  if (!self.refLines)
    return;

  // Erase all the reference lines
  self.vis.selectAll("g.ref").remove();

  // Redraw the reference gamma lines
  self.drawRefGammaLines();
}

SpectrumChartD3.prototype.clearReferenceLines = function() {
  var self = this;

  // No need to clear, we don't have any data
  if (!self.refLines)
    return;

  self.refLines = null;
  self.redraw()();
}

SpectrumChartD3.prototype.setReferenceLines = function( data ) {
  var self = this;
  self.vis.selectAll("g.ref").remove();
 
  var default_colors = ["#0000FF","#006600", "#006666", "#0099FF","#9933FF", "#FF66FF", "#CC3333", "#FF6633","#FFFF99", "#CCFFCC", "#0000CC", "#666666", "#003333"];

  var index = 0;
  if( !data ){
    this.refLines = null;
  } else {
    try {
      if( !Array.isArray(data) )
        throw "Input is not an array of reference lines";

      data.forEach( function(a,i){
         if( !a.color )
           a.color = default_colors[i%default_colors.length];
         if( !a.lines || !Array.isArray(a.lines) )
           throw "Reference lines does not contain an array of lines";
         a.lines.forEach( function(d){
           d.id = ++index;  //We need to assign an ID to use as D3 data, that is unique (energy may not be unique)
           
           /*{e:30.27,h:6.22e-05,particle:'xray',decay:'xray',el:'barium'} */
           /*particle in ["gamma", "xray", "beta", "alpha",   "positron", "electronCapture"]; */
           if( (typeof d.e !== "number") || (typeof d.h !== "number") || (typeof d.particle !== "string") )
             throw "Refernce line is invalid (" + JSON.stringify(d) + ")";
         });
       });

    /*this.refLines = JSON.parse(JSON.stringify(data));  /*creates deep copy, but then also have to go through and */
    this.refLines = data;
    this.refLines.forEach( function(a,i){ a.lines.forEach( function(d){ d.parent = a; } ) } );
  }catch(e){
    this.refLines = null;
    console.log( "invalid input to setReferenceLines" );
  }
    this.refLines = data;
  }

  this.redraw()();
}

SpectrumChartD3.prototype.setShowRefLineInfoForMouseOver = function( show ) {
  var self = this;

  self.options.showRefLineInfoForMouseOver = show;
  self.redraw()();
}


/**
 * -------------- Grid Lines Functions --------------
 */
SpectrumChartD3.prototype.setGridX = function( onstate ) {
  if( this.options.gridx == onstate )
    return;

  this.options.gridx = onstate;

  if( onstate ) {
    this.xGrid = d3.svg.axis().scale(this.xScale)
                   .orient("bottom")
                   .innerTickSize(-this.size.height)
                   .outerTickSize(0)
                   .tickFormat( "" )
                   .tickPadding(10)
                   .ticks( 20,"" );

    this.xGridBody = this.vis.insert("g", ".refLineInfo")
        .attr("width", this.size.width )
        .attr("height", this.size.height )
        .attr("class", "xgrid" )
        .attr("transform", "translate(0," + this.size.height + ")")
        .call( this.xGrid );
  } else {
    if( this.xGridBody )
      this.xGridBody.remove();
    this.xGrid = null;
    this.xGridBody = null;
  }

  this.redraw(true)();
}

SpectrumChartD3.prototype.setGridY = function( onstate ) {
  if( this.options.gridy == onstate )
    return;

  this.options.gridy = onstate;

  if( onstate ) {
    this.yGrid = d3.svg.axis().scale(this.yScale)
                   .orient("left")
                   .innerTickSize(-this.size.width)
                   .outerTickSize(0)
                   .tickFormat( "" )
                   .tickPadding(10);

    this.yGridBody = this.vis.insert("g", ".refLineInfo")
        .attr("width", this.size.width )
        .attr("height", this.size.height )
        .attr("class", "ygrid" )
        .attr("transform", "translate(0,0)")
        .call( this.yGrid );
  } else {
    this.yGridBody.remove();
    this.yGrid = null;
    this.yGridBody = null;
  }

  this.redraw()();
}


/**
 * -------------- Mouse Coordinate Info Functions --------------
 */
SpectrumChartD3.prototype.addMouseInfoBox = function(){
  if( this.mouseInfo )
    this.mouseInfo.remove();

  this.mouseInfo = this.vis.append("g")
                     .attr("class", "mouseInfo")
                     .style("display", "none")
                     .attr("transform","translate(" + this.size.width + "," + this.size.height + ")");

  this.mouseInfoBox = this.mouseInfo.append('rect')
               .attr("class", "mouseInfoBox")
               .attr('width', "12em")
               .attr('height', "2.5em")
               .attr('x', "-12.5em")
               .attr('y', "-3.1em");

  this.mouseInfo.append("g").append("text");
}

SpectrumChartD3.prototype.updateMouseCoordText = function() {
  var self = this;

  if ( !d3.event || !self.rawData || !self.rawData.spectra || !self.rawData.spectra.length )
    return;

  var p = d3.mouse(self.vis[0][0]);
  /* console.log("fix mouse text"); */

  if( !p ){
    p = d3.touch(self.vis[0][0]);
    p =  (p && p.length===1) ? p[0] : null;
  }

  if( !p ){
    self.mousedOverRefLine = null;
    self.refLineInfo.style("display", "none");
    self.mouseInfo.style("display", "none");
    return;
  }

  var energy = self.xScale.invert(p[0]);
  var y = self.yScale.invert(p[1]);

  /*Find what channel this energy cooresponds */
  var channel, lowerchanval, counts = null, backgroundSubtractCounts = null;
  var foreground = self.rawData.spectra[0];
  var background = self.getSpectrumByID(foreground.backgroundID);
  var bisector = d3.bisector(function(d){return d.x;});
  channel = (foreground.x && foreground.x.length) ? d3.bisector(function(d){return d;}).right(foreground.x, energy) : -1;
  if( foreground.points && foreground.points.length ){
    lowerchanval = bisector.left(foreground.points,energy,1) - 1;
    counts = foreground.points[lowerchanval].y; 
  }
  if (self.options.backgroundSubtract && counts !== null && background) {
    lowerchanval = bisector.left(background.points,energy,1) - 1;
    backgroundSubtractCounts = Math.max(0, counts - (background.points[lowerchanval] ? background.points[lowerchanval].y : 0));
  }

  /*console.log( "updateMouseCoordText: {" + energy + "," + y + "} and also fix self.refLines[0] usage"); */

  /*Currently two majorish issues with the mouse text */
  /*  1) The counts for the foreground are all that is given. Should give for background/second */
  /*  2) Currently gives a channel (singular), but when there this.rebinFactor!=1, should give range */
  /*Also, formatting could be a bit better */
  /*Also need to make displaying this box an option */
  /*Could also add a blue dot in the data or something, along with lines to the axis, both features should be optional */

  /*Right now if mouse stats arent deesired we are just not showing them, but */
  /*  still updating them... */

  if( self.options.showMouseStats ){
    self.mouseInfo.style("display", null );
    var mousetxt = self.mouseInfo.select("text");
    mousetxt.attr('dy', "-2em");
    mousetxt.selectAll("tspan").remove();

    var xmmsg = ""+(Math.round(10*energy)/10) + " keV";
    if( channel )
      xmmsg += ", chan: " + channel;
    var ymmsg = "";
    if( counts !== null )
      ymmsg += "counts: " + (Math.round(10*counts)/10) + (foreground.rebinFactor === 1 ? "" : ("/" + foreground.rebinFactor));
    ymmsg += (counts!==null?", ":"") + "y: " + (Math.round(10*y)/10);
    var bgsubmsg = "";
    if( backgroundSubtractCounts !== null )
      bgsubmsg += "counts (BG sub): " + (Math.round(10*backgroundSubtractCounts)/10) + (foreground.rebinFactor === 1 ? "" : ("/" + foreground.rebinFactor));

    var bgsubmsglen = 0;
    if (backgroundSubtractCounts !== null)
      bgsubmsglen = mousetxt.append('svg:tspan').attr('x', "-12em").attr('dy', "-1em")
                      .text( bgsubmsg ).node().getComputedTextLength();


    var ymmsglen = mousetxt.append('svg:tspan').attr('x', "-12em").attr('dy', "-1em")
                    .text( ymmsg ).node().getComputedTextLength();
    var xmmsglen = mousetxt.append('svg:tspan').attr('x', "-12em").attr('dy', "-1em")
            .text( xmmsg ).node().getComputedTextLength();

    /*Resize the box to match the text size */
    self.mouseInfoBox.attr('width', Math.max(xmmsglen,ymmsglen,bgsubmsglen) + 9 )
      .attr('height', backgroundSubtractCounts !== null ? '3.1em' : '2.5em')
      .attr('y', backgroundSubtractCounts !== null ? '-3.9em' : '-3.1em');
  } else {
    self.mouseInfo.style("display", "none" );
  }

  var mindist = 9.0e20, nearestpx = 9.0e20;

  var nearestline = null;
  var h = self.size.height;
  var m = Math.min(h,self.options.refLineTopPad);
  var visy = Math.max(h-m,1);

  var reflines = self.vis.selectAll("g.ref");

  reflines[0].forEach( function(d,i){
    var yh = d.childNodes[0].y1.baseVal.value - d.childNodes[0].y2.baseVal.value;
    /*var xpx = d.transform.baseVal[0].matrix.e; */
    var xpx = self.xScale(d.__data__.e);
    var dpx = Math.abs(xpx - p[0]);

    /*In principle, this check (or __data__.mousedover) shouldnt be necassary, */
    /*  but with out it sometimes lines will stay fat that arent supposed to. */
    /* Also, I think setting attr values is expensive, so only doing if necassary. */
    if( d.__data__.mousedover && d !== self.mousedOverRefLine ){
      d3.select(d).attr("stroke-width",1).attr("dx", "-0.5" );
      d.__data__.mousedover = null;
    }

    var dist = dpx + dpx/(yh/visy);
    if( dist < mindist ) {
      mindist = dist;
      nearestline = d;
      nearestpx = dpx;
    }
  } );

  if( nearestpx > 10 ) {
    if( self.mousedOverRefLine ){
      d3.select(self.mousedOverRefLine).attr("stroke-width",1).attr("dx", "-0.5" );
      self.mousedOverRefLine.__data__.mousedover = null;
    }
    self.mousedOverRefLine = null;
    self.refLineInfo.style("display", "none");
    return;
  }

  if( self.mousedOverRefLine===nearestline )
    return;

  if( self.mousedOverRefLine ){
    d3.select(self.mousedOverRefLine).attr("stroke-width",1).attr("dx", "-0.5" );
    self.mousedOverRefLine.__data__.mousedover = null;
  }

  self.mousedOverRefLine = nearestline;

  var linedata = nearestline.__data__;
  linedata.mousedover = true;
  var e = linedata.e;
  var sf = linedata.h;
  var linepx = self.xScale(e);

  var txt, textdescrip, attTxt;
  var detector = linedata.parent.detector
  var shielding = linedata.parent.shielding;
  var shieldingThickness = linedata.parent.shieldingThickness;
  var nearestLineParent = linedata.parent.parent;


  /*20160308: self.refLines[0] should now contain member variable particleSf */
  /*  that gives a map from the particle name to the scale factor applied to */
  /*  get sf. ex: var abs_br = self.refLines[0].particleSf[linedata.particle] * sf. */

  textdescrip = (nearestLineParent ? (nearestLineParent + ', ') : "") +  e + ' keV, rel. amp. ' + sf;

  if( linedata.decay ) {
    if( linedata.particle === 'gamma' ) {
      txt = linedata.decay;
      if( linedata.decay.indexOf('Capture') < 0 )
        txt += ' decay';
    }else if( linedata.particle === 'xray' ) {
      textdescrip = linedata.el + ' x-ray, ' +  e + ' keV, I=' + sf;
    }else if( (typeof linedata.particle === 'string') && linedata.particle.length ){
      textdescrip = linedata.particle + ' from ' + nearestLineParent + ", " +  e + ' keV, I=' + sf;
    }
  }

  if( linedata.particle === 'gamma' || linedata.particle === 'xray' ) {
    if( shielding && shieldingThickness )
      attTxt = shieldingThickness + ' of ' + shielding;
    if( detector )
      attTxt = (attTxt ? (attTxt + ' with a ' + detector) : 'Assuming a ' + detector);
  }

  self.refLineInfo.style("display", null).attr("transform", "translate("+linepx+",0)" );
  var svgtxt = self.refLineInfoTxt.select("text")
                   .attr("dy", "1em")
                   .attr("fill", linedata.parent.color);
  svgtxt.selectAll("tspan").remove();
  if ( self.options.showRefLineInfoForMouseOver ) {
    svgtxt.append('svg:tspan').attr('x', 0).attr('dy', "1em").text( textdescrip );
    if( txt )
      svgtxt.append('svg:tspan').attr('x', 0).attr('dy', "1em").text( txt );
    if( attTxt )
      svgtxt.append('svg:tspan').attr('x', 0).attr('dy', "1em").text( attTxt );

    /*Now detect if svgtxt is running off the right side of the chart, and if so */
    /*  put to the left of the line */
    var tx = function(d) {
      var w = this.getBBox().width;
      return ((linepx+5+w)>self.size.width) ? ("translate("+(-5-w)+",0)") : "translate(5,0)";
    };
    self.refLineInfoTxt.attr("transform", tx );
  }


  d3.select(nearestline).attr("stroke-width",2).select("line").attr("dx", "-1" );
}

SpectrumChartD3.prototype.setShowMouseStats = function(d) {
  this.options.showMouseStats = d;
  this.mouseInfo.style("display", d ? null : "none");
  if( d )
    this.updateMouseCoordText();
}


/**
 * -------------- Legend Functions --------------
 */
SpectrumChartD3.prototype.updateLegend = function() {
  var self = this;
  
  if( !this.options.showLegend || !self.rawData || !self.rawData.spectra || !self.rawData.spectra.length ) {
    if( this.legend ) {
      this.legend.remove();
      this.legend = null;
      this.legendBox = null;
      this.legBody = null;
      this.legendHeaderClose = null;
      //Not emmitting 'legendClosed' since self.options.showLegend is not being changed.
      //self.WtEmit(self.chart.id, {name: 'legendClosed'} );
    }
    return;
  }
  
  if( !this.legend ) {

    function moveleg(){                 /* move legend  */
      if( self.legdown ) {
        /* console.log(d3.event); */
        d3.event.preventDefault();
        d3.event.stopPropagation();

        var x = d3.event.x ? d3.event.x : d3.event.touches ?  d3.event.touches[0].clientX : d3.event.clientX;
        var y = d3.event.y ? d3.event.y : d3.event.touches ?  d3.event.touches[0].clientY : d3.event.clientY;

        var calculated_x = d3.mouse(self.vis[0][0])[0];

        if ( calculated_x >= -self.padding.leftComputed && y >= 0 && 
             calculated_x <= self.cx && y <= self.cy ) {
          //console.log("change pos");
          var tx = (x - self.legdown.x) + self.legdown.x0;
          var ty = (y - self.legdown.y) + self.legdown.y0; 
          self.legend.attr("transform", "translate(" + tx + "," + ty + ")");
        }
      }
    }


    this.legend = d3.select(this.chart).select("svg").append("g")
                      .attr("class", "legend")
                      .attr("transform","translate(" + (this.cx - 120 - this.padding.right) + ","+ (this.padding.topComputed + 10) + ")");
    this.legendBox = this.legend.append('rect')
               .attr("class", "legendBack")
               .attr('width', "100")
               .attr('height', "1em")
               .attr( "rx", "5px")
               .attr( "ry", "5px");
    this.legBody = this.legend.append("g")
                       .attr("transform","translate(8,17)");
                       
    this.legendHeader = this.legend.append("g"); 
    this.legendHeader
               .style("display", "none")
               .append('rect')
               .attr("class", "legendHeader")
               .attr('width', "100px")
               .attr('height', "1.5em")
               .attr( "rx", "5px")
               .attr( "ry", "5px")
               .style("cursor", "pointer");
    
    /*Add a close button to get rid of the legend */
    this.legendHeaderClose = this.legendHeader.append('g').attr("transform","translate(4,4)");
    this.legendHeaderClose.append("rect")
            .attr("class", "d3closebut")
            .attr('height', "12")
            .attr('width', "12");
    this.legendHeaderClose.append("path")
        .attr("style", "stroke: white; stroke-width: 1.5px;" )
        .attr("d", "M 2,2 L 10,10 M 10,2 L 2,10");
    this.legendHeaderClose.on("click", function(){ 
      self.options.showLegend = false; 
      self.updateLegend(); 
      self.WtEmit(self.chart.id, {name: 'legendClosed'} );
    } ).on("touchend", function(){ 
      self.options.showLegend = false; 
      self.updateLegend(); 
      self.WtEmit(self.chart.id, {name: 'legendClosed'} );
    } );   
               
    /*this.legendHeader.append("text") */
    /*      .text("Legend") */
    /*      .attr("x", 62.5) */
    /*      .attr("y", "1.1em") */
    /*      .style("text-anchor","middle") */
    /*      .style("cursor", "pointer"); */
    
    this.legend.on("mouseover", function(d){if( !self.dragging_plot && !self.zooming_plot ) self.legendHeader.style("display", null);} )
      .on("mouseout", function(d){self.legendHeader.style("display", "none");} )
      .on("mousemove", moveleg)
      .on("touchmove", moveleg)
      .on("wheel", function(d){d3.event.preventDefault(); d3.event.stopPropagation();} );
    
    function mousedownleg(){
      //console.log("mouse down on legend");
      if (d3.event.defaultPrevented) return;
      if( self.dragging_plot || self.zooming_plot ) return;
      d3.event.preventDefault();
      d3.event.stopPropagation();
      var trans = d3.transform(self.legend.attr("transform")).translate;

      var x = d3.event.x ? d3.event.x : d3.event.touches ?  d3.event.touches[0].clientX : d3.event.clientX;
      var y = d3.event.y ? d3.event.y : d3.event.touches ?  d3.event.touches[0].clientY : d3.event.clientY;
      self.legdown = {x: x, y: y, x0: trans[0], y0: trans[1]};
    };
    
    this.legendHeader.on("mouseover", function(d) { if( !self.dragging_plot && !self.zooming_plot ) self.legend.attr("class", "legend activeLegend");} )
      .on("touchstart", function(d) { if( !self.dragging_plot && !self.zooming_plot ) self.legend.attr("class", "legend activeLegend"); } )
      .on("mouseout",  function(d) { if (self.legend) self.legend.attr("class", "legend"); } )
      .on("touchend",  function(d) { if (self.legend) self.legend.attr("class", "legend"); } )
      .on("mousedown.drag",  mousedownleg )
      .on("touchstart.drag",  mousedownleg )
      .on("touchend.drag", function() {self.legdown = null;})
      .on("mouseup.drag", function(){self.legdown = null;} )
      .on("mousemove.drag", moveleg)
      .on("mouseout.drag", moveleg);

    this.legend.on("touchstart", function(d) { if( !self.dragging_plot && !self.zooming_plot ) self.legendHeader.style("display", null); } )
      .on("touchstart.drag", mousedownleg)
      .on("touchend.drag",  function() 
      {
      if (!self.legend || !self.legendHeader) {
        self.legdown = null;
        return;
      }

      self.legend.attr("class", "legend"); 
      window.setTimeout(function() { self.legendHeader.style("display", "none"); }, 1500) 
      self.legdown = null; 
      });
  }
  
  var origtrans = d3.transform(this.legend.attr("transform")).translate;
  var bb = this.legend.node().getBBox();
  var fromRight = this.cx - origtrans[0] - this.legendBox.attr('width');
  
  this.legBody.selectAll("g").remove();

  var ypos = 0;
  const spectra = self.rawData ? self.rawData.spectra : [];
  spectra.forEach( function(spectrum,i){
    if( !spectrum || !spectrum.y.length )
      return;
      
    const sf = ((typeof spectrum.yScaleFactor === "number") ? spectrum.yScaleFactor: 1);
    const lt = spectrum.liveTime;
    const rt = spectrum.realTime;
    const neutsum = spectrum.neutrons;
      
    const nsum = sf*spectrum.dataSum;
    const title = (spectrum.title ? spectrum.title : ("Spectrum " + (i+1)))
                    + " (" + nsum.toFixed(nsum > 1000 ? 0 : 1) + " counts)";
    
    let thisentry = self.legBody.append("g")
        .attr("transform","translate(0," + ypos + ")");
      
    thisentry.append("path")
        //.attr("id", "spectrum-legend-line-" + i)  // reference for when updating color
        //.attr("class", "line" )
        .attr("stroke", spectrum.lineColor ? spectrum.lineColor : "black")
        .attr("stroke-width", self.options.spectrumLineWidth )
        .attr("fill", 'none' )
        .attr("d", "M0,-5 L12,-5");
      
    let thistxt = thisentry.append("text")
        .attr("class", "legentry")
        .attr( "x", 15 )
        .text(title);
        
    if( typeof lt === "number" )
      thistxt.append('svg:tspan')
        .attr('x', "20")
        .attr('y', thisentry.node().getBBox().height)
        .text( "Live Time: " + (sf*lt).toPrecision(4) + " s" );
      
    if( typeof rt === "number" )
      thistxt.append('svg:tspan')
        .attr('x', "20")
        .attr('y', thisentry.node().getBBox().height)
        .text( "Real Time: " + (sf*rt).toPrecision(4) + " s");
          
    if( sf != 1 )
      thistxt.append('svg:tspan')
        .attr('x', "20")
        .attr('y', thisentry.node().getBBox().height)
        .text( "Scaled by " + sf.toPrecision(4) );
          
    if( typeof neutsum === "number" ){
      // \TODO: spectrum.neutronRealTime is currently never set by SpecUtils/InterSpec, but will be once parsing
      //        sepearte neutron real times is implemented.
      const nrt = (typeof spectrum.neutronRealTime === "number") ? spectrum.neutronRealTime : rt;
      const isCps = (typeof nrt === "number");
      const neut = isCps ? neutsum/nrt : neutsum*sf;
      
        
      // Lets print the neutron counts as a human friendly number, to roughly
      //   the precision we would care about.  Could probably do a much better
      //   with less code, but whatever for now.
      let toLegendRateStr = function( val, ndig ){
        const powTen = Math.floor(Math.log10(Math.abs(val)));
        
        if( Number.isInteger(val) || Number.isNaN(ndig) || Number.isNaN(powTen) )  //Write integers out as integers
          return '' + val;
        else if( (powTen < -4) || (powTen > ndig) )        //Numbers less than 0.0001, use scientific notation, ex. 6.096e-6 (where ndig==3)
          return '' + val.toExponential(ndig);
        else if( powTen < 3 )         //Numbers between 0.0001 and 1000, ex. 0.06096 (where ndig==3)
          return '' + val.toFixed(ndig-powTen);
        else                          //Numbers greater than 1000 just write as integer
          return '' + val.toFixed(0);
      };//toLegendRateStr
        
        
      let neutspan = thistxt.append('svg:tspan')
              .attr('x', "20")
              .attr('y', thisentry.node().getBBox().height)
              .text( "Neutrons: " + toLegendRateStr(neut,3) + (isCps ? " cps" : ""));
      
      //If we are displaying neutron CPS, and this is not a foreground, then lets add an easy way to compare this rate
      //  to the foreground
      if( isCps
          && (spectrum.type === self.spectrumTypes.FOREGROUND)
          || (spectrum.type === self.spectrumTypes.SECONDARY) )
      {
        //Get the neutron info for the foreground; note uses first foreground
        let forNeut = null, forNeutLT = null;
        
        for( let j = 0; j < spectra.length; ++j )
        {
          const spec = spectra[j];
          if( spec && (j !== i)
              && (spec.type === self.spectrumTypes.BACKGROUND)
              && ((typeof spec.neutronRealTime === "number") || (typeof spec.realTime === "number"))
              && (typeof spec.neutrons === "number") )
          {
            forNeut = spec.neutrons;
            forNeutLT = (typeof spec.neutronRealTime === "number") ? spec.neutronRealTime : spec.realTime;
            break;
          }
        }//for( loop over spectrum )
         
        if( (typeof forNeut === "number") && (typeof forNeutLT === "number") && (neutsum>0 || forNeut>0) )
        {
          const forRate = forNeut/forNeutLT;
          const forRateSigma = Math.sqrt(forNeut) / forNeutLT;
          const rateSigma = Math.sqrt(neutsum) / nrt;
          const sigma = Math.sqrt(rateSigma*rateSigma + forRateSigma*forRateSigma);
          const nsigma = Math.abs(neut - forRate) / sigma;
          const isneg = (neut < forRate);
          
          thistxt.append('svg:tspan')
            .attr('x', "40")
            .attr('y', thisentry.node().getBBox().height - 4)
            .attr('style', 'font-size: 75%')
            .html( "(" + toLegendRateStr(nsigma,1) + " &sigma; " + (isneg ? "below" : "above") + " background)" );
        }//if( we have foreground neutron CPS info )
      }//if( this is not a foreground, and we are displaying neutron CPS )
      
      
      //It would be nice to display the total neutron
      if( isCps ){
        thisentry.neutinfo = thistxt.append('svg:tspan')
          .attr('x', "40")
          .attr('y', thisentry.node().getBBox().height - 5)
          .attr('style', 'display: none')
          .text( toLegendRateStr(neutsum,3) + " neutrons" + (typeof rt === "number" ? (" in " + rt.toPrecision(4) + " s") : "") );
      
        neutspan
          .on("mouseover", function(){
            thisentry.neutinfo.attr('style', 'font-size: 75%' )
            self.legendBox.attr('height', self.legBody.node().getBBox().height + 10 );
          } )
          .on("mouseout", function(){
            thisentry.neutinfo.attr('style', 'display: none;')
            self.legendBox.attr('height', self.legBody.node().getBBox().height + 10 );
          });
       }// if( is CPS instead of sum neutrons )
      
    }//if( typeof neut === "number" )
      
    ypos += thisentry.node().getBBox().height + 5;
  });//spectra.forEach
  
                    
  /*Resize the box to match the text size */
  var w = this.legBody.node().getBBox().width + 15; 
  this.legendBox.attr('width', w );
  this.legendBox.attr('height', this.legBody.node().getBBox().height + 10 );
  this.legendHeaderClose.attr("transform","translate(" + (w-16) + ",4)");
  
  this.legendHeader.select('rect').attr('width', w );
  this.legendHeader.select('text').attr("x", w/2);
  
  /*this.legendBox.attr('height', legtxt.node().getBBox().height + hh + 8 ); */

  /*Set the transform so the space on the right of the legend stays the same */
  this.legend.attr("transform", "translate(" + (this.cx - fromRight - w) + "," + origtrans[1] + ")" );
}

SpectrumChartD3.prototype.setShowLegend = function( show ) {
  this.options.showLegend = Boolean(show);
  this.updateLegend();
}


/**
 * -------------- Y-axis Functions --------------
 */
SpectrumChartD3.prototype.yticks = function() {
  var ticks = [];
  var EPSILON = 1.0E-3;

  // Added check for raw data to not render ticks when no data is present
  if (!this.rawData || !this.rawData.spectra) return [];

  var formatYNumber = function(v) {
    /*poorly simulating "%.3g" in snprintf */
    /*SHould get rid of so many regexs, and shorten code (shouldnt there be a builtin function to print to "%.3"?) */
    var t;
    if( v >= 1000 || v < 0.1 )
    {
      t = v.toPrecision(3);
      t = t.replace(/\.0+e/g, "e").replace(/\.0+$/g, "");
      if( t.indexOf('.') > 0 )
        t = t.replace(/0+e/g, "e");
    } else {
      t = v.toFixed( Math.max(0,2-Math.floor(Math.log10(v))) );
      if( t.indexOf('.') > 0 )
        t = t.replace(/0+$/g, "");
      t = t.replace(/\.$/g, "");
    }

    return t;
  }

  var renderymin = this.yScale.domain()[1],
      renderymax = this.yScale.domain()[0],
      heightpx = this.size.height;
  var range = renderymax - renderymin;

  if( this.options.yscale === "lin" )
  {
    /*px_per_div: pixels between major and/or minor labels. */
    var px_per_div = 50;

    /*nlabel: approx number of major + minor labels we would like to have. */
    var nlabel = heightpx / px_per_div;

    /*renderInterval: Inverse of how many large labels to place between powers */
    /*  of 10 (1 is none, 0.5 is is one). */
    var renderInterval;

    /*n: approx how many labels will be used */
    var n = Math.pow(10, Math.floor(Math.log10(range/nlabel)));

    /*msd: approx how many sub dashes we would expect there to have to be */
    /*     to satisfy the spacing of labels we want with the given range. */
    var msd = range / nlabel / n;

    if( isNaN(n) || !isFinite(n) || nlabel<=0 || n<=0.0 ) { /*JIC */
      console.log( "n=" + n + ", nlabel=" + nlabel + ", range=" + range );
      return ticks;
    }
      var subdashes = 0;

      if( msd < 1.5 )
      {
        subdashes = 2;
        renderInterval = 0.5*n;
      }else if (msd < 3.3)
      {
        subdashes = 5;
        renderInterval = 0.5*n;
      }else if (msd < 7)
      {
        subdashes = 5;
        renderInterval = n;
      }else
      {
        subdashes = 10;
        renderInterval = n;
      }

      var biginterval = subdashes * renderInterval;
      var starty = biginterval * Math.floor((renderymin + 1.0E-15) / biginterval);

      if( starty < (renderymin-EPSILON*renderInterval) )
        starty += biginterval;

      for( var i = -Math.floor(Math.floor(starty-renderymin)/renderInterval); ; ++i)
      {
        if( i > 500 )  /*JIC */
          break;

        var v = starty + renderInterval * i;

        if( (v - renderymax) > EPSILON * renderInterval )
          break;

        var t = "";
        if( i>=0 && ((i % subdashes) == 0) )
          t += formatYNumber(v);

        var len = ((i % subdashes) == 0) ? true : false;

        ticks.push( {value: v, major: len, text: t } );
      }/*for( intervals to draw ticks for ) */
    }/*case Chart::LinearScale: */

    if( this.options.yscale === "log" )
    {
      /*Get the power of 10 just below or equal to rendermin. */
      var minpower = (renderymin > 0.0) ? Math.floor( Math.log10(renderymin) ) : -1;

      /*Get the power of 10 just above or equal to renderymax.  If renderymax */
      /*  is less than or equal to 0, set power to be 0. */
      var maxpower = (renderymax > 0.0) ? Math.ceil( Math.log10(renderymax) ): 0;

      /*Adjust minpower and maxpower */
      if( maxpower == minpower )
      {
        /*Happens when renderymin==renderymax which is a power of 10 */
        ++maxpower;
        --minpower;
      }else if( maxpower > 2 && minpower < -1)
      {
        /*We had a tiny value (possibly a fraction of a count), as well as a */
        /*  large value (>1000). */
        minpower = -1;
      }else if( maxpower >= 0 && minpower < -1 && (maxpower-minpower) > 6 )
      {
        /*we had a tiny power (1.0E-5), as well as one between 1 and 999, */
        /*  so we will only show the most significant decades */
        minpower = maxpower - 5;
      }/*if( minpower == maxpower ) / else / else */


      /*numdecades: number of decades the data covers, including the decade */
      /*  above and below the data. */
      var numdecades = maxpower - minpower + 1;

      /*minpxdecade: minimum number of pixels we need per decade. */
      var minpxdecade = 25;

      /*labeldelta: the number of decades between successive labeled large ticks */
      /*  each decade will have a large tick regardless */
      var labeldelta = 1;

      /*nticksperdecade: number of small+large ticks per decade */
      var nticksperdecade = 10;


      if( Math.floor(heightpx / minpxdecade) < numdecades )
      {
        labeldelta = numdecades / (heightpx / minpxdecade);
        nticksperdecade = 1;
      }/*if( (heightpx / minpxdecade) < numdecades ) */

      var t = null;
      var nticks = 0;
      var nmajorticks = 0;

      for( var decade = minpower; decade <= maxpower; ++decade )
      {
        var startcounts = Math.pow( 10.0, decade );
        var deltacounts = 10.0 * startcounts / nticksperdecade;
        var eps = deltacounts * EPSILON;

        if( (startcounts - renderymin) > -eps && (startcounts - renderymax) < eps )
        {
          t = ((decade%labeldelta)==0) ? formatYNumber(startcounts) : "";
          ++nticks;
          ++nmajorticks;
          ticks.push( {value: startcounts, major: true, text: t } );
        }/*if( startcounts >= renderymin && startcounts <= renderymax ) */


        for( var i = 1; i < (nticksperdecade-1); ++i )
        {
          var y = startcounts + i*deltacounts;
          if( (y - renderymin) > -eps && (y - renderymax) < eps )
          {
            ++nticks;  
            ticks.push( {value: y, major: false, text: null } );
          }
        }/*for( int i = 1; i < nticksperdecade; ++i ) */
      }/*for( int decade = minpower; decade <= maxpower; ++decade ) */

      /*If we have a decent number of (sub) labels, the user can orient */
      /*  themselves okay, so well get rid of the minor labels. */
      if( (nticks > 8 || (heightpx/nticks) < 25 || nmajorticks > 1) && nmajorticks > 0 ) {
        for( var i = 0; i < ticks.length; ++i )
          if( !ticks[i].major )
            ticks[i].label = "";
      }
      
      if( nmajorticks < 1 && ticks.length ) {
        ticks[0].text = formatYNumber(ticks[0].value);
        ticks[ticks.length-1].text = formatYNumber(ticks[ticks.length-1].value);
      }
      
      if( ticks.length === 0 )
      {
        /*cerr << "Forcing a single axis point in" << endl; */
        var y = 0.5*(renderymin+renderymax);
        var t = formatYNumber(y);
        ticks.push( {value: y, major: true, text: t } );
      }
    }/*case Chart::LogScale: */

  /*TODO: should to properly implement sqrt */
  if( this.options.yscale === "sqrt" ){
    /*Take the easy way out for now until I can get around to customizing */
    this.yScale.copy().ticks(10)
        .forEach(function(e){ticks.push({value:e,major:true,text:formatYNumber(e)});});
  }


  return ticks;
}

/* Sets y-axis drag for the chart. These are actions done by clicking and dragging one of the labels of the y-axis. */
SpectrumChartD3.prototype.yaxisDrag = function(d) {
  var self = this;
  return function(d) {
    console.log('yaxisDrag work');
    document.onselectstart = function() { return false; };
    var p = d3.mouse(self.vis[0][0]);
    self.yaxisdown = self.yScale.invert(p[1]);
  }
}

SpectrumChartD3.prototype.drawYTicks = function() {
  var self = this;
  var stroke = function(d) { return d ? "#ccc" : "#666"; };
  
  /* Regenerate y-ticks… */
    var ytick = self.yticks();
    var ytickvalues = ytick.map(function(d){return d.value;} );
    self.yScale.ticks(ytickvalues);

    self.yAxisBody.selectAll('text').remove();

    if( self.yGridBody ) {
      self.yGrid.tickValues( ytickvalues );

      /*Since the number of grid lines might change (but call(self.yGrid) expects the same number) */
      /*  we will remove, and re-add back in the grid... kinda a hack. */
      /*  Could probably go back to manually drawing the grid lined and get rid */
      /*  of yGrid and yGridBody... */
      self.yGridBody.remove();
      self.yGridBody = self.vis.insert("g", ".refLineInfo")
        .attr("width", self.size.width )
        .attr("height", self.size.height )
        .attr("class", "ygrid" )
        .attr("transform", "translate(0,0)")
        .call( self.yGrid );
      self.yGridBody.selectAll('g.tick')
        .filter(function(d,i){return !ytick[i].major;} )
        .attr("class","minorgrid");
    }

    //If self.yScale(d) will return a NaN, then exit this function anyway
    if( self.yScale.domain()[0]===self.yScale.domain()[1] ){
      self.vis.selectAll("g.y").remove();
      return;
    }

    var ty = function(d) { return "translate(0," + self.yScale(d) + ")"; };
    var gy;

    gy = self.vis.selectAll("g.y")
      .data(ytickvalues, String)
      .attr("transform", ty);


    var fy = function(d,i){ return ytick[i].text; }; /*self.yScale.tickFormat(10); */
    gy.select("text").text( fy );

    var gye = gy.enter().insert("g", "a")
        .attr("class", "y")
        .attr("transform", ty)
        .attr("background-fill", "#FFEEB6");

    gye.append("line")
       .attr("stroke", stroke)
       .attr("class", "yaxistick")
       .attr("x1", function(d,i){ return ytick[i].major ? -7 : -4; } )
       .attr("x2", 0 );

    gye.append("text")
        .attr("class", "yaxislabel")
        .attr("x", -8.5)
        .attr("dy", ".35em")
        .attr("text-anchor", "end")
        .text(fy);
        /* .style("cursor", "ns-resize") */
        /* .on("mouseover", function(d) { d3.select(this).style("font-weight", "bold");}) */
        /* .on("mouseout",  function(d) { d3.select(this).style("font-weight", "normal");}); */
        /* .on("mousedown.drag",  self.yaxisDrag()) */
        /* .on("touchstart.drag", self.yaxisDrag()); */

    gy.exit().remove();
}

SpectrumChartD3.prototype.setAdjustYAxisPadding = function( adjust, pad ) {
  this.options.adjustYAxisPadding = Boolean(adjust);
  
  if( typeof pad === "number" )
    this.padding.left = pad;
    
  this.handleResize( false );
}

SpectrumChartD3.prototype.setWheelScrollYAxis = function(d) {
  this.options.wheelScrollYAxis = d;
}


/**
 * -------------- Y-axis Scale Functions --------------
 */
SpectrumChartD3.prototype.setLogY = function(){
  /*To make the transition animated, see: http:/*bl.ocks.org/benjchristensen/2657838 */

  if( this.options.yscale === "log" )
    return;

  this.options.yscale = "log";

  this.yScale = d3.scale.log()
      .clamp(true)
      .domain([0, 100])
      .nice()
      .range([1, this.size.height])
      .nice();

  if( this.yGrid )
    this.yGrid.scale( this.yScale );

  this.redraw(this.options.showAnimation)();
}

SpectrumChartD3.prototype.setLinearY = function(){
  if( this.options.yscale === "lin" )
    return;

  this.options.yscale = "lin";
  this.yScale = d3.scale.linear()
      .domain([0, 100])
      .nice()
      .range([0, this.size.height])
      .nice();

  if( this.yGrid )
    this.yGrid.scale( this.yScale );

  this.redraw(this.options.showAnimation)();
}

SpectrumChartD3.prototype.setSqrtY = function(){
  if( this.options.yscale === "sqrt" )
    return;

  this.options.yscale = "sqrt";
  this.yScale = d3.scale.pow().exponent(0.5)
      .domain([0, 100])
      .range([0, this.size.height]);

  if( this.yGrid )
    this.yGrid.scale( this.yScale );

  this.redraw(this.options.showAnimation)();
}


SpectrumChartD3.prototype.handleYAxisWheel = function() {
  /*This function doesnt have the best behaviour in the world, but its a start */
  var self = this;
  /* console.log("handleYAxisWheel"); */
  
  if( !d3.event )
    return;
    
  var m = d3.mouse(this.vis[0][0]);
  var t = d3.touches(this.vis[0][0]);

  if( m[0] > 0 && !t )
    return false;
  
  var wdelta;
  /* wdelta = d3.event.wheelDelta == null ? d3.event.sourceEvent.wheelDelta : d3.event.wheelDelta;  /* old way using source events */
  wdelta = d3.event.deltaY ? d3.event.deltaY : d3.event.sourceEvent ? d3.event.sourceEvent.wheelDelta : 0;

  /* Implementation for touch interface */
  /* if (!wdelta && wdelta !== 0) { */
  /*   var t1,t2,dx,dy; */

  /*   t1 = t[0]; */
  /*   t2 = t[1]; */

  /*   dy = Math.abs(t1[1] - t2[1]); */

  /*   wdelta = self.previous_dy - dy; */
  /* } */

  
  var mult = 0;
  if( wdelta > 0 ){
    /*zoom out */
    mult = 0.02;
  } else if( wdelta != 0 ) {
    /*zoom in */
    mult = -0.02;
  }

  if( self.options.yscale == "log" ) {
    
    if( mult > 0 && self.options.logYFracBottom > 0.025 ){
      self.options.logYFracBottom -= mult;
    } else {
      self.options.logYFracTop += mult;
      self.options.logYFracTop = Math.min( self.options.logYFracTop, 10 );  
    }
    
    if( self.options.logYFracTop < 0 ){
      self.options.logYFracBottom += -self.options.logYFracTop;
      self.options.logYFracBottom = Math.min( self.options.logYFracBottom, 2.505 );
      self.options.logYFracTop = 0;
    }
  
    self.options.logYFracTop = Math.max( self.options.logYFracTop, -0.95 );
  } else if( self.options.yscale == "lin" ) {
    self.options.linYFracTop += mult;
    self.options.linYFracTop = Math.min( self.options.linYFracTop, 0.85 );
    self.options.linYFracTop = Math.max( self.options.linYFracTop, -0.95 );
    /*self.options.linYFracBottom = 0.1; */
  } else if( self.options.yscale == "sqrt" ) {
    self.options.sqrtYFracTop += mult;
    self.options.sqrtYFracTop = Math.min( self.options.sqrtYFracTop, 0.85 );
    self.options.sqrtYFracTop = Math.max( self.options.sqrtYFracTop, -0.95 );
    /*self.options.sqrtYFracBottom = 0.1;   */
  }            
            
  self.redraw()();
  
  if( d3.event.sourceEvent ){       
   d3.event.sourceEvent.preventDefault();
   d3.event.sourceEvent.stopPropagation();
  } else {
    d3.event.preventDefault();
    d3.event.stopPropagation();
  }
  return false;
}


/**
 * -------------- X-axis Functions --------------
 */
SpectrumChartD3.prototype.xticks = function() {

  var ticks = [];

  /*it so */
  /*  the x axis labels (hopefully) always line up nicely where we want them */
  /*  e.g. kinda like multiple of 5, 10, 25, 50, 100, etc. */
  var EPSILON = 1E-3;

  var rendermin = this.xScale.domain()[0];
  var rendermax = this.xScale.domain()[1];
  var range = rendermax - rendermin;
  
  /*ndigstart makes up for larger numbers taking more pixels to render, so */
  /* it keeps numbers from overlapping.  Below uses 15 to kinda rpresent the */
  /*  width of numbers in pixels. */
  var ndigstart = rendermin > 0 ? Math.floor(Math.log10(rendermin)) : 1;
  ndigstart = Math.max(1,Math.min(ndigstart,5));
  
  var nlabel = Math.floor( this.size.width / (50 + 15*(ndigstart-1)) );

  
  var renderInterval;/* = range / 10.0; */
  var n = Math.pow(10, Math.floor(Math.log10(range/nlabel)));
  var msd = range / (n * nlabel);


  if( isNaN(n) || !isFinite(n) || nlabel<=0 || n<=0.0 ) { /*JIC */
    console.log( "n=" + n + ", nlabel=" + nlabel + ", range=" + range );
    return ticks;
  }

  var subdashes = 0;

  /*console.log( "msd=" + msd + ", nlabel=" + nlabel + ", ndigstart=" + ndigstart ); */

  if (msd < 1.5)
  {
    subdashes = 2;
    renderInterval = 0.5*n;
  }else if (msd < 3.3)
  {
    subdashes = 5;
    renderInterval = 0.5*n;
  }else if (msd < 7)
  {
    subdashes = 5;
    renderInterval = n;
  }else
  {
    subdashes = 10;
    renderInterval = n;
  }

  var biginterval = subdashes * renderInterval;
  var startEnergy = biginterval * Math.floor((rendermin + 1.0E-15) / biginterval);

  if( startEnergy < (rendermin-EPSILON*renderInterval) )
    startEnergy += biginterval;

  for( var i = -Math.floor(Math.floor(startEnergy-rendermin)/renderInterval); ; ++i)
  {
    if( i > 5000 )  /*JIC */
      break;

    var v = startEnergy + renderInterval * i;

    if( (v - rendermax) > EPSILON * renderInterval )
      break;

    var t = "";
    if( i>=0 && (i % subdashes == 0) )
      t += v;

    ticks.push( {value: v, major: (i % subdashes == 0), text: t } );
  }/*for( intervals to draw ticks for ) */

  return ticks;
}

/* Sets x-axis drag for the chart. These are actions done by clicking and dragging one of the labels of the x-axis. */
SpectrumChartD3.prototype.xaxisDrag = function() {
  
  var self = this;
  return function(d) {
    /*This function is called once when you click on an x-axis label (which you can then start dragging it) */
    /*  And NOT when you click on the chart and drag it to pan */

    document.onselectstart = function() { return false; };
    var p = d3.mouse(self.vis[0][0]);

    if (self.xScale.invert(p[0]) > 0){           /* set self.xaxisdown equal to value of your mouse pos */
      self.xaxisdown = [self.xScale.invert(p[0]), self.xScale.domain()[0], self.xScale.domain()[1]];
    }
  }
}

SpectrumChartD3.prototype.drawXAxisArrows = function(show_arrow) {
  var self = this;

  if (self.options.showXRangeArrows) {
    var max_x;

    if (!self.xaxis_arrow) {
      self.xaxis_arrow = self.svg.select('.xaxis').append('svg:defs')
        .attr("id", "xaxisarrowdef")
        .append("svg:marker")
        .attr("id", "arrowhead")
        .attr('class', 'xaxisarrow')
        .attr("refX", 0)
        .attr("refY", 6)
        .attr("markerWidth", 9)
        .attr("markerHeight", 14)
        .attr("orient", 0)
        .append("path")
          .attr("d", "M2,2 L2,13 L8,7 L2,2")
          .style("stroke", "black");
    }

    max_x = self.min_max_x_values()[1];

    if (!self.rawData || !self.rawData.spectra || !self.rawData.spectra.length || self.xScale.domain()[1] === max_x || (typeof show_arrow == 'boolean' && !show_arrow))            /* should be a better way to determine if can still pan */
      self.xAxisBody.select("path").attr("marker-end", null);
    else
      self.xAxisBody.select("path").attr("marker-end", "url(#arrowhead)");

  } else {
    if (self.xaxis_arrow) {
      self.xaxis_arrow.remove();
      self.xaxis_arrow = null;
    }

    self.svg.select("#xaxisarrowdef").remove();
  }
}

SpectrumChartD3.prototype.drawXTicks = function() {
  var self = this;
  var stroke = function(d) { return d ? "#ccc" : "#666"; };
  
  var xticks = self.xticks();
  var xtickvalues = xticks.map(function(d){return d.value;} );
  self.xAxis.tickValues( xtickvalues );
     
  /**
   * Regenerate x-ticks…
   * Christian [032818]: Commented out for performance improvement, D3 will reuse current tick nodes when
   *  using new axis tick values, so we don't need to remove the current ones
   */
  // self.xAxisBody.selectAll("g.tick").remove();

  self.xAxisBody.call(self.xAxis);

  /*Check that the last tick doesnt go off the chart area. */
  /*  This could probably be accomplished MUCH more efficiently */
  var xgticks = self.xAxisBody.selectAll('g.tick');
  var majorticks = xgticks.filter(function(d,i){ return xticks[i] && xticks[i].major; } );
  var minorticks = xgticks.filter(function(d,i){ return xticks[i] && !xticks[i].major; } );

  minorticks.select('line').attr('y2', '4');
  minorticks.select('text').text("");

  /**
   * Christian [032818]: Made a slight performance optimization by moving the D3 select assignment code
   * for styles and event listeners to major ticks. This still achieves the same result, but prevents wasted operations
   * by assigning the styles and event listeners to ticks that are actually displayed. Noticable improvements seen
   * when using w/InterSpec.
   */
  //const majorticksText = majorticks.selectAll('text')
  //  .style("cursor", "ew-resize")
  //  .on("mouseover", function(d, i) { d3.select(this).style("font-weight", "bold");})
  //  .on("mouseout",  function(d) { d3.select(this).style("font-weight", null);})
  //  .on("mousedown.drag",  self.xaxisDrag());

  // Add touch event listeners for touch devices
  //if (self.isTouchDevice()) {
  //  majorticksText.on("touchstart.drag", self.xaxisDrag());
  //}

  if( this.options.compactXAxis && self.xaxistitle ){
    /* We have to check every tick to see if it overlaps with the title */
    var xtitlex = self.xaxistitle.attr("x" );
    majorticks[0].forEach( function(tick){
      var txt = d3.select(tick).select('text')[0][0]; 
      if( (txt.getCTM().e + txt.getBBox().width) + 30 > xtitlex )  /*Not sure why we need this 30, but its in positioning of the x-axis title too */
        d3.select(txt)
        .text("");
    });
  } else {
    /*We only need to check the last tick to see if it goes off the chart */
    const majorticksText = majorticks.selectAll('text');
    var lastmajor = majorticks[0].length ? majorticks[0][majorticks[0].length-1] : null; 
    if( lastmajor ) {
      lastmajor = d3.select(lastmajor).select('text')[0][0];
      if( (lastmajor.getCTM().e + lastmajor.getBBox().width) > this.cx )
        d3.select(lastmajor).text("");  
    }
  }
  /*this.options.compactXAxis */
  
  /*Can calculate the width needed for the y-axis, and could adjust the plot area.. */
  /*console.log( self.yAxisBody.node().getBBox().width ); */

  if( self.xGridBody ) {
    self.xGrid.tickValues( xtickvalues );
    self.xGridBody.remove();
    self.xGridBody = self.vis.insert("g", ".refLineInfo")
          .attr("width", self.size.width )
          .attr("height", self.size.height )
          .attr("class", "xgrid" )
          .attr("transform", "translate(0," + self.size.height + ")")
          .call( self.xGrid );
    self.xGridBody.selectAll('g.tick')
      .filter(function(d,i){ return !xticks[i].major; } )
      .attr("class","minorgrid");
  }
}

SpectrumChartD3.prototype.setXAxisRange = function( minimum, maximum, doEmit ) {
  var self = this;

  self.xScale.domain([minimum, maximum]);

  if( doEmit )
    self.WtEmit(self.chart.id, {name: 'xrangechanged'}, minimum, maximum, self.size.width, self.size.height);
}

SpectrumChartD3.prototype.setXAxisMinimum = function( minimum ) {
  var self = this;

  const maximum = self.xScale.domain()[1];

  self.xScale.domain([minimum, maximum]);
  self.redraw()();
}

SpectrumChartD3.prototype.setXAxisMaximum = function( maximum ) {
  var self = this;

  const minimum = self.xScale.domain()[0];

  self.xScale.domain([minimum, maximum]);
  self.redraw()();
}

SpectrumChartD3.prototype.setXRangeArrows = function(d) {
  var self = this;
  this.options.showXRangeArrows = d;
  this.drawXAxisArrows(d);
}

SpectrumChartD3.prototype.setCompactXAxis = function( compact ) {
  this.options.compactXAxis = Boolean(compact);
  
  /*Might want to add ability to change xTitlePad here.  */
  /*this.padding.xTitlePad = 10; */
    
  this.handleResize( false );
}


/**
 * -------------- Chart Pan (X-axis) Slider Functions --------------
 */
SpectrumChartD3.prototype.drawXAxisSliderChart = function() {
  var self = this;
  
  // Cancel if the chart or raw data are not present
  if (!self.chart || d3.select(self.chart).empty() || !self.rawData
    || !self.rawData.spectra || !self.rawData.spectra.length || self.size.height<=0 ) {
    self.cancelXAxisSliderChart();
    return;
  }
    
  // Cancel the action and clean up if the option for the slider chart is not checked
  if( !self.options.showXAxisSliderChart ) {
    self.cancelXAxisSliderChart();
    return;
  }

  function drawDragRegionLines() {
    d3.selectAll(".sliderDragRegionLine").remove();
    
    if (!self.sliderDragLeft || !self.sliderDragRight) {
      return;
    }
    var leftX = Number(self.sliderDragLeft.attr("x"));
    var leftY = Number(self.sliderDragLeft.attr("y"));
    var leftWidth =  Number(self.sliderDragLeft.attr("width"));
    var leftHeight = self.sliderDragLeft[0][0].height.baseVal.value;
    var rightX = Number(self.sliderDragRight.attr("x"));
    var rightY = Number(self.sliderDragRight.attr("y"));
    var rightWidth =  Number(self.sliderDragRight.attr("width"));
    var rightHeight = self.sliderDragRight[0][0].height.baseVal.value;

    var numberOfLines = 4;

    for (var i = 1; i < numberOfLines; i++) {
      self.sliderChart.append('line')
        .attr("class", "sliderDragRegionLine")
        .style("fill", "#444")
        .attr("stroke", "#444" )
        .attr("stroke-width", "0.08%")
        .attr("x1", leftX + (i*leftWidth)/numberOfLines)
        .attr("x2", leftX + (i*leftWidth)/numberOfLines)
        .attr("y1", leftY + (leftHeight/4))
        .attr("y2", leftY + (3*leftHeight/4))
        .on("mousedown", self.handleMouseDownLeftSliderDrag())
        .on("mousemove", self.handleMouseMoveLeftSliderDrag(false))
        .on("mouseout", self.handleMouseOutLeftSliderDrag())
        .on("touchstart", self.handleTouchStartLeftSliderDrag())
        .on("touchmove", self.handleTouchMoveLeftSliderDrag(false));

      self.sliderChart.append('line')
        .attr("class", "sliderDragRegionLine")
        .style("fill", "#444")
        .attr("stroke", "#444" )
        .attr("stroke-width", "0.08%")
        .attr("x1", rightX + (i*rightWidth)/numberOfLines)
        .attr("x2", rightX + (i*rightWidth)/numberOfLines)
        .attr("y1", rightY + (rightHeight/4))
        .attr("y2", rightY + (3*rightHeight/4))
        .on("mousedown", self.handleMouseDownRightSliderDrag())
        .on("mousemove", self.handleMouseMoveRightSliderDrag(false))
        .on("mouseout", self.handleMouseOutRightSliderDrag())
        .on("touchstart", self.handleTouchStartRightSliderDrag())
        .on("touchmove", self.handleTouchMoveRightSliderDrag(false));
    }
  }

  // Store the original x and y-axis domain (we'll use these to draw the slider lines and position the slider box)
  var origdomain = self.xScale.domain();
  var origdomainrange = self.xScale.range();
  var origrange = self.yScale.domain();
  var bounds = self.min_max_x_values();
  var maxX = bounds[1];
  var minX = bounds[0];

  // Change the x and y-axis domain to the full range (for slider lines)
  self.xScale.domain([minX, maxX]);
  self.xScale.range([0, self.size.sliderChartWidth]);
  self.do_rebin();
  self.rebinForBackgroundSubtract();
  self.yScale.domain(self.getYAxisDomain());

  let axiscolor = null;
  
  // Draw the elements for the slider chart
  if( !self.sliderChart ) {
    axiscolor = 'black';
    const tickElement = document.querySelector('.tick');
    const tickStyle = tickElement ? getComputedStyle(tickElement) : null;
    axiscolor = tickStyle && tickStyle.stroke ? tickStyle.stroke : 'black';
    
    // G element of the slider chart
    self.sliderChart = d3.select("svg").append("g")
      //.attr("transform", "translate(" + self.padding.leftComputed + "," + (this.chart.clientHeight - self.size.sliderChartHeight) + ")")
      // .on("mousemove", self.handleMouseMoveSliderChart());
      .on("touchstart", self.handleTouchStartSliderChart())
      .on("touchmove", self.handleTouchMoveSliderChart());

    // Plot area for data lines in slider chart
    self.sliderChartPlot = self.sliderChart.append("rect")
      .attr("id", "sliderchartarea"+self.chart.id )
      .style("opacity","0.1")
      .style("fill", axiscolor);
      //.style("fill", "#EEEEEE");

    // Chart body for slider (keeps the data lines)
    self.sliderChartBody = self.sliderChart.append("g")
      .attr("clip-path", "url(#sliderclip" + this.chart.id + ")");

    // Clip path for slider chart
    self.sliderChartClipPath = self.sliderChart.append('svg:clipPath')
        .attr("id", "sliderclip" + self.chart.id )
        .append("svg:rect")
        .attr("x", 0)
        .attr("y", 0);

    // For adding peaks into slider chart 
    // self.sliderPeakVis = self.sliderChart.append('g')
    //   .attr("id", "sliderPeakVis")
    //   .attr("class", "peakVis")
    //   .attr("transform", "translate(0,0)")
    //   .attr("clip-path", "url(#sliderclip" + this.chart.id + ")");

  }

  self.sliderChartPlot.attr("width", self.size.sliderChartWidth)
      .attr("height", self.size.sliderChartHeight);
  self.sliderChartClipPath.attr("width", self.size.sliderChartWidth)
      .attr("height", self.size.sliderChartHeight);
  self.sliderChart
      .attr("transform", "translate(" + 0.5*(self.cx - self.size.sliderChartWidth) + "," + (this.chart.clientHeight - self.size.sliderChartHeight) + ")");
  
  // Commented out for adding peaks into slider chart sometime later
  // self.sliderPeakVis.selectAll('*').remove();
  // self.peakVis.select(function() {
  //   this.childNodes.forEach(function(path) {
  //     path = d3.select(path);
  //     self.sliderPeakVis.append('path')
  //       .attr("d", path.attr('d'))
  //       .attr("class", path.attr('class'))
  //       .attr("fill-opacity", path.attr('fill-opacity'))
  //       .attr("stroke-width", path.attr('stroke-width'))
  //       .attr("stroke", path.attr("stroke"))
  //       .attr("transform", "translate(0," + (self.size.height + extraPadding + self.padding.sliderChart) + ")");
  //   });
  // });

  // Add the slider draggable box and edges
  if (!self.sliderBox) {
    if( !axiscolor ){
      axiscolor = 'black';
      const tickElement = document.querySelector('.tick');
      const tickStyle = tickElement ? getComputedStyle(tickElement) : null;
      axiscolor = tickStyle && tickStyle.stroke ? tickStyle.stroke : 'black';
    }
    
    // Slider box
    self.sliderBox = self.sliderChart.append("rect")
      .attr("class", "sliderBox")
      .style("fill-opacity","0.5")
      .style("fill", axiscolor)
      .attr("stroke", axiscolor)
      .attr("stroke-width", "0.2%" )
      .on("mousedown", self.handleMouseDownSliderBox())
      .on("touchstart", self.handleTouchStartSliderBox())
      .on("touchmove", self.handleTouchMoveSliderChart());

    // Left slider drag region
    self.sliderDragLeft = self.sliderChart.append("rect")
      .attr("id", "sliderDragLeft")
      .attr("class", "sliderDragRegion")
      .attr("rx", 2)
      .attr("ry", 2)
      .style("fill-opacity","0.1")
      .style("fill", axiscolor)
      .attr("stroke",axiscolor)
      .attr("stroke-width", "0.1%" )
      .on("mousedown", self.handleMouseDownLeftSliderDrag())
      .on("mousemove", self.handleMouseMoveLeftSliderDrag(false))
      .on("mouseout", self.handleMouseOutLeftSliderDrag())
      .on("touchstart", self.handleTouchStartLeftSliderDrag())
      .on("touchmove", self.handleTouchMoveLeftSliderDrag(false));

    // Right slider drag region
    self.sliderDragRight = self.sliderChart.append("rect")
      .attr("id", "sliderDragRight")
      .attr("class", "sliderDragRegion")
      .attr("rx", 2)
      .attr("ry", 2)
      .style("fill-opacity","0.1")
      .style("fill", axiscolor)
      .attr("stroke",axiscolor)
      .attr("stroke-width", "0.1%" )
      .on("mousedown", self.handleMouseDownRightSliderDrag())
      .on("mousemove", self.handleMouseMoveRightSliderDrag(false))
      .on("mouseout", self.handleMouseOutRightSliderDrag())
      .on("touchstart", self.handleTouchStartRightSliderDrag())
      .on("touchmove", self.handleTouchMoveRightSliderDrag(false));
  }

  var sliderBoxX = self.xScale(origdomain[0]);
  var sliderBoxWidth = self.xScale(origdomain[1]) - sliderBoxX;

  // Adjust the position of the slider box to the particular zoom region
  self.sliderBox.attr("x", sliderBoxX)
    .attr("width", sliderBoxWidth)
    .attr("height", self.size.sliderChartHeight);
    // .on("mousemove", self.handleMouseMoveSliderChart());

  self.sliderDragLeft.attr("width", self.size.sliderChartWidth/100)
    .attr("height", self.size.sliderChartHeight/2.3);
  self.sliderDragRight.attr("width", self.size.sliderChartWidth/100)
    .attr("height", self.size.sliderChartHeight/2.3);

  self.sliderDragLeft.attr("x", sliderBoxX - Number(self.sliderDragLeft.attr("width"))/2)
    .attr("y", self.size.sliderChartHeight/2 - Number(self.sliderDragLeft.attr("height"))/2);

  self.sliderDragRight.attr("x", (sliderBoxX + sliderBoxWidth) - (Number(self.sliderDragRight.attr("width"))/2))
    .attr("y", self.size.sliderChartHeight/2 - Number(self.sliderDragRight.attr("height"))/2);

  self.drawSliderChartLines();
  drawDragRegionLines();

  // Restore the original x and y-axis domain
  self.xScale.domain(origdomain);
  self.xScale.range(origdomainrange);
  self.do_rebin();
  self.rebinForBackgroundSubtract();
  self.yScale.domain(origrange);
}

SpectrumChartD3.prototype.drawSliderChartLines = function()  {
  var self = this;

  // Cancel the action and clean up if the option for the slider chart is not checked or there is no slider chart displayed
  if( !self.options.showXAxisSliderChart || !self.sliderChartBody || !self.rawData || !self.rawData.spectra )
    return;

  // Delete the data lines if they are present
  for (let i = 0; i < self.rawData.spectra.length; ++i) {
    //console.log(self['sliderLine' + i]);
    if (self['sliderLine' + i])
      self['sliderLine' + i].remove();
  }

  for (let i = 0; i < self.rawData.spectra.length; ++i) {
    let spectrum = self.rawData.spectra[i];
    if (self.options.backgroundSubtract && spectrum.type == self.spectrumTypes.BACKGROUND) continue;

    if (self['line'+i] && self.size.height>0 && self.size.sliderChartHeight>0 )
      self['sliderLine'+i] = self.sliderChartBody.append("path")
        .attr("id", 'sliderLine'+i)
        .attr("class", 'sline sliderLine')
        .attr("stroke", spectrum.lineColor ? spectrum.lineColor : 'black')
        .attr("d", self['line'+i](spectrum[self.options.backgroundSubtract ? 'bgsubtractpoints' : 'points']))
        .attr("transform","scale(1," + (self.size.sliderChartHeight / self.size.height) + ")");
  }
}

SpectrumChartD3.prototype.cancelXAxisSliderChart = function() {
  var self = this;

  if( !self.sliderChart )
    return;

  var height = Number(d3.select(this.chart)[0][0].style.height.substring(0, d3.select(this.chart)[0][0].style.height.length - 2));

  
  if (self.sliderChart) {
    self.sliderChart.remove();
    self.sliderChartBody.remove();
    self.sliderChartPlot.remove();  
    self.sliderChartClipPath.remove();
    self.sliderBox.remove();
    self.svg.selectAll(".sliderDragRegion").remove();

    if (self.rawData && self.rawData.spectra && self.rawData.spectra.length)
      for (var i = 0; i < self.rawData.spectra.length; ++i)
        if (self['sliderLine'+i]) {
          self['sliderLine'+i].remove();
          self['sliderLine'+i] = null;
        }

    self.sliderChart = null;
    self.sliderChartPlot = null;
    self.sliderChartBody = null;
    self.sliderChartClipPath = null;
    self.sliderBox = null;
  }

  self.sliderBoxDown = false;
  self.leftDragRegionDown = false;
  self.rightDragRegionDown = false;
  self.sliderChartMouse = null;
  self.savedSliderMouse = null;
  
  this.handleResize( false );
}

SpectrumChartD3.prototype.setShowXAxisSliderChart = function(d) {
  this.options.showXAxisSliderChart = d;
  this.drawXAxisSliderChart();
  this.handleResize( false );
}

SpectrumChartD3.prototype.handleMouseDownSliderBox = function() {
  var self = this;

  return function() {
    /* In order to stop selection of text around chart when clicking down on slider box. */
    d3.event.preventDefault();
    d3.event.stopPropagation();

    self.sliderBoxDown = true;
    self.leftDragRegionDown = false;
    self.rightDragRegionDown = false;

    /* Initially set the escape key flag false */
    /* ToDo: record initial range so if escape is pressed, can reset to it */
    self.escapeKeyPressed = false;    

    d3.select(document.body).style("cursor", "move");
  }
}

SpectrumChartD3.prototype.handleMouseMoveSliderChart = function() {
  var self = this;

  return function() {
    d3.event.preventDefault();
    d3.event.stopPropagation();
    /* console.log("sliderboxdown = ", self.sliderBoxDown); */
    /* console.log("leftDragRegionDown = ", self.leftDragRegionDown); */
    /* console.log("rightDragRegionDown = ", self.rightDragRegionDown); */

    if (self.leftDragRegionDown) {
      return self.handleMouseMoveLeftSliderDrag(true)();
    }

    if (self.rightDragRegionDown) {
      return self.handleMouseMoveRightSliderDrag(true)();
    }

    if (self.sliderBoxDown) {
      d3.select(document.body).style("cursor", "move");
      var m = d3.mouse(self.sliderChart[0][0]);
      var origdomain = self.xScale.domain();
      var origdomainrange = self.xScale.range();
      var bounds = self.min_max_x_values();
      var maxX = bounds[1];
      var minX = bounds[0];

      if (!self.sliderChartMouse) {
        self.sliderChartMouse = m;
      }

      var sliderBoxX = Number(self.sliderBox.attr("x"));
      var sliderBoxWidth = Number(self.sliderBox.attr("width"));
      var sliderDragRegionWidth = 3;
      var x = Math.min( self.size.sliderChartWidth - sliderBoxWidth, Math.max(0, sliderBoxX + (m[0] - self.sliderChartMouse[0])) );

      if ((sliderBoxX == 0 || sliderBoxX + sliderBoxWidth == self.size.sliderChartWidth)) {
        if (!self.savedSliderMouse)
          self.savedSliderMouse = m;
      }

      if (self.savedSliderMouse && m[0] != self.savedSliderMouse[0]) {
        if (sliderBoxX == 0 && m[0] < self.savedSliderMouse[0]) return;
        else if (sliderBoxX + sliderBoxWidth == self.size.sliderChartWidth && m[0] > self.savedSliderMouse[0]) return;
        else self.savedSliderMouse = null;
      }

      self.xScale.domain([minX, maxX]);
      self.xScale.range([0, self.size.sliderChartWidth]);
      self.sliderBox.attr("x", x);
      self.sliderDragLeft.attr("x", x);
      self.sliderDragRight.attr("x", x + sliderBoxWidth - sliderDragRegionWidth);

      origdomain = [ self.xScale.invert(x), self.xScale.invert(x + sliderBoxWidth) ];
      self.setXAxisRange(origdomain[0], origdomain[1],true);
      self.xScale.range(origdomainrange);
      self.redraw()();

      self.sliderChartMouse = m;
    }
  }
}

SpectrumChartD3.prototype.handleMouseDownLeftSliderDrag = function() {
  var self = this;

  return function() {
    /* In order to stop selection of text around chart when clicking down on slider box. */
    d3.event.preventDefault();
    d3.event.stopPropagation();

    self.leftDragRegionDown = true;

    /* Initially set the escape key flag false */
    self.escapeKeyPressed = false;    
  }
}

SpectrumChartD3.prototype.handleMouseMoveLeftSliderDrag = function(redraw) {
  var self = this;

  return function() {
    d3.event.preventDefault();
    d3.event.stopPropagation();

    if (self.sliderBoxDown) {
      return self.handleMouseMoveSliderChart()();
    }

    d3.select(document.body).style("cursor", "ew-resize");

    if (!self.leftDragRegionDown || !redraw) {
      return;
    }

    var m = d3.mouse(self.sliderChart[0][0]);
    var origdomain = self.xScale.domain();
    var origdomainrange = self.xScale.range();
    var bounds = self.min_max_x_values();
    var maxX = bounds[1];
    var minX = bounds[0];
    var x = Math.max(m[0], 0);

    var sliderBoxX = self.xScale(origdomain[0]);
    var sliderBoxWidth = Number(self.sliderBox.attr("width"));
    var sliderDragRegionWidth = 3;
    var sliderDragPadding = 1;

    self.xScale.domain([minX, maxX]);
    self.xScale.range([0, self.size.sliderChartWidth]);

    if (m[0] > Number(self.sliderDragRight.attr("x") - sliderDragPadding)) {
      self.xScale.domain(origdomain);
      return;
    }

    self.sliderBox.attr("x", x);
    self.sliderDragLeft.attr("x", x);
    origdomain[0] = self.xScale.invert(x);

    self.setXAxisRange(origdomain[0], origdomain[1],true);
    self.xScale.range(origdomainrange);
    self.redraw()();
  }
}

SpectrumChartD3.prototype.handleMouseOutLeftSliderDrag = function() {
  var self = this;

  return function() {
    if (!self.leftDragRegionDown) {
      d3.select(document.body).style("cursor", "default");
    }
  }
}

SpectrumChartD3.prototype.handleMouseDownRightSliderDrag = function() {
  var self = this;

  return function() {
    /* In order to stop selection of text around chart when clicking down on slider box. */
    d3.event.preventDefault();
    d3.event.stopPropagation();

    self.rightDragRegionDown = true;

    /* Initially set the escape key flag false */
    self.escapeKeyPressed = false;    
  }
}

SpectrumChartD3.prototype.handleMouseMoveRightSliderDrag = function(redraw) {
  var self = this;

  return function() {

    if (self.sliderBoxDown) {
      return; /*self.handleMouseMoveSliderChart()(); */
    }

    d3.event.preventDefault();
    d3.event.stopPropagation();
    d3.select('body').style("cursor", "ew-resize");

    if (!self.rightDragRegionDown || !redraw) {
      return;
    }

    var m = d3.mouse(self.sliderChart[0][0]);
    var origdomain = self.xScale.domain();
    var origdomainrange = self.xScale.range();
    var bounds = self.min_max_x_values();
    var maxX = bounds[1];
    var minX = bounds[0];
    var x = Math.min(m[0], self.size.sliderChartWidth);

    var sliderBoxX = self.xScale(origdomain[0]);
    var sliderBoxWidth = Number(self.sliderBox.attr("width"));
    var sliderDragRegionWidth = 3;
    var sliderDragPadding = 1;

    self.xScale.domain([minX, maxX]);
    self.xScale.range([0, self.size.sliderChartWidth]);

    if (m[0] - sliderDragRegionWidth < Number(self.sliderDragLeft.attr("x")) + Number(self.sliderDragLeft.attr("width"))) {
      self.xScale.domain(origdomain);
      self.xScale.range(origdomainrange);
      return;
    }

    self.sliderBox.attr("width", Math.abs(x - Number(self.sliderDragRight.attr("x"))));
    self.sliderDragRight.attr("x", x - sliderDragRegionWidth);
    origdomain[1] = self.xScale.invert(x);

    self.setXAxisRange(origdomain[0], origdomain[1], true);
    self.xScale.range(origdomainrange);
    self.redraw()();
  }
}

SpectrumChartD3.prototype.handleMouseOutRightSliderDrag = function() {
  var self = this;

  return function() {
    if (!self.rightDragRegionDown) {
      d3.select(document.body).style("cursor", "default");
    }
  }
}

SpectrumChartD3.prototype.handleTouchStartSliderBox = function() {
  var self = this;

  return function() {
    d3.event.preventDefault();
    d3.event.stopPropagation();

    self.sliderBoxDown = true;
    self.leftDragRegionDown = false;
    self.rightDragRegionDown = false;

    var t = [d3.event.pageX, d3.event.pageY];
    var touchError = 25;
    var x1 = self.sliderBox[0][0].getBoundingClientRect().left;
    var x2 = self.sliderBox[0][0].getBoundingClientRect().right;

    if (d3.event.changedTouches.length !== 1)
      return;

    if (x1 - touchError <= t[0] && t[0] <= x1 + touchError) {
      self.sliderBoxDown = false;
      self.leftDragRegionDown = true;

    } else if (x2 - touchError <= t[0] && t[0] <= x2 + touchError) {
      self.sliderBoxDown = false;
      self.rightDragRegionDown = true;
    }
  }
}

SpectrumChartD3.prototype.handleTouchStartSliderChart = function() {
  var self = this;

  return function() {
    var t = [d3.event.pageX, d3.event.pageY];
    var touchError = 15;
    var x1 = self.sliderBox[0][0].getBoundingClientRect().left;
    var x2 = self.sliderBox[0][0].getBoundingClientRect().right;

    if (d3.event.changedTouches.length !== 1)
      return;

    if (x1 - touchError <= t[0] && t[0] <= x1 + touchError) {
      self.sliderBoxDown = false;
      self.leftDragRegionDown = true;

    } else if (x2 - touchError <= t[0] && t[0] <= x2 + touchError) {
      self.sliderBoxDown = false;
      self.rightDragRegionDown = true;
    }
  }
}

SpectrumChartD3.prototype.handleTouchMoveSliderChart = function() {
  var self = this;

  return function() {
    d3.event.preventDefault();
    d3.event.stopPropagation();

    if (self.leftDragRegionDown) {
      return self.handleTouchMoveLeftSliderDrag(true)();
    }

    if (self.rightDragRegionDown) {
      return self.handleTouchMoveRightSliderDrag(true)();
    }

    if (self.sliderBoxDown) {
      d3.select(document.body).style("cursor", "move");
      var t = d3.touches(self.sliderChart[0][0]);

      if (t.length !== 1)
        return;

      t = t[0];
      var origdomain = self.xScale.domain();
      var origdomainrange = self.xScale.range();
      var bounds = self.min_max_x_values();
      var maxX = bounds[1];
      var minX = bounds[0];

      if (!self.sliderChartTouch) {
        self.sliderChartTouch = t;
      }

      var sliderBoxX = Number(self.sliderBox.attr("x"));
      var sliderBoxWidth = Number(self.sliderBox.attr("width"));
      var sliderDragRegionWidth = 3;
      var x = Math.min( self.size.sliderChartWidth - sliderBoxWidth, Math.max(0, sliderBoxX + (t[0] - self.sliderChartTouch[0])) );

      if ((sliderBoxX == 0 || sliderBoxX + sliderBoxWidth == self.size.sliderChartWidth)) {
        if (!self.savedSliderTouch)
          self.savedSliderTouch = t;
      }

      if (self.savedSliderTouch && t[0] != self.savedSliderTouch[0]) {
        if (sliderBoxX == 0 && t[0] < self.savedSliderTouch[0]) return;
        else if (sliderBoxX + sliderBoxWidth == self.size.sliderChartWidth && t[0] > self.savedSliderTouch[0]) return;
        else self.savedSliderTouch = null;
      }

      self.xScale.domain([minX, maxX]);
      self.xScale.range([0, self.size.sliderChartWidth]);
      self.sliderBox.attr("x", x);
      self.sliderDragLeft.attr("x", x);
      self.sliderDragRight.attr("x", x + sliderBoxWidth - sliderDragRegionWidth);

      origdomain = [ self.xScale.invert(x), self.xScale.invert(x + sliderBoxWidth) ];
      self.setXAxisRange(origdomain[0], origdomain[1], true);
      self.xScale.range(origdomainrange);
      self.redraw()();

      self.sliderChartTouch = t;

      /* IMPORTANT: To translate the current x-scale into the current zoom object */
      self.zoom.x(self.xScale);
    }
  }
}

SpectrumChartD3.prototype.handleTouchStartLeftSliderDrag = function() {
  var self = this;

  return function() {
    self.leftDragRegionDown = true;
  }
}

SpectrumChartD3.prototype.handleTouchMoveLeftSliderDrag = function(redraw) {
  var self = this;

  return function() {
    d3.event.preventDefault();
    d3.event.stopPropagation();

    if (self.sliderBoxDown) {
      return;
    }

    if (!self.leftDragRegionDown) {
      return;
    }

    var t = d3.touches(self.sliderChart[0][0]);
    if (t.length !== 1)
      return;

    t = t[0];
    var origdomain = self.xScale.domain();
    var origdomainrange = self.xScale.range();
    var bounds = self.min_max_x_values();
    var maxX = bounds[1];
    var minX = bounds[0];
    var x = Math.max(t[0], 0);

    var sliderBoxX = self.xScale(origdomain[0]);
    var sliderBoxWidth = Number(self.sliderBox.attr("width"));
    var sliderDragRegionWidth = 3;
    var sliderDragPadding = 1;

    self.xScale.domain([minX, maxX]);
    self.xScale.range([0, self.size.sliderChartWidth]);

    if (t[0] > Number(self.sliderDragRight.attr("x") - sliderDragPadding)) {
      self.xScale.domain(origdomain);
      return;
    }

    self.sliderBox.attr("x", x);
    self.sliderDragLeft.attr("x", x);
    origdomain[0] = self.xScale.invert(x);

    self.setXAxisRange(origdomain[0], origdomain[1], true);
    self.xScale.range(origdomainrange);
    self.redraw()();

    /* IMPORTANT: To translate the current x-scale into the current zoom object */
    self.zoom.x(self.xScale);
  }
}

SpectrumChartD3.prototype.handleTouchStartRightSliderDrag = function() {
  var self = this;

  return function() {
    self.rightDragRegionDown = true;
  }
}

SpectrumChartD3.prototype.handleTouchMoveRightSliderDrag = function(redraw) {
  var self = this;

  return function() {
    if (self.sliderBoxDown) {
      return;
    }

    d3.event.preventDefault();
    d3.event.stopPropagation();

    if (!self.rightDragRegionDown) {
      return;
    }

    var t = d3.touches(self.sliderChart[0][0]);
    if (t.length !== 1)
      return;
  
    t = t[0];
    var origdomain = self.xScale.domain();
    var origdomainrange = self.xScale.range();
    var bounds = self.min_max_x_values();
    var maxX = bounds[1];
    var minX = bounds[0];
    var x = Math.min(t[0], self.size.sliderChartWidth);

    var sliderBoxX = self.xScale(origdomain[0]);
    var sliderBoxWidth = Number(self.sliderBox.attr("width"));
    var sliderDragRegionWidth = 3;
    var sliderDragPadding = 1;

    self.xScale.domain([minX, maxX]);
    self.xScale.range([0, self.size.sliderChartWidth]);

    if (t[0] - sliderDragRegionWidth < Number(self.sliderDragLeft.attr("x")) + Number(self.sliderDragLeft.attr("width"))) {
      self.xScale.domain(origdomain);
      self.xScale.range(origdomainrange);
      return;
    }

    self.sliderBox.attr("width", Math.abs(x - Number(self.sliderDragRight.attr("x"))));
    self.sliderDragRight.attr("x", x - sliderDragRegionWidth);
    origdomain[1] = self.xScale.invert(x);

    self.setXAxisRange(origdomain[0], origdomain[1], true);
    self.xScale.range(origdomainrange);
    self.redraw()();

    /* IMPORTANT: To translate the current x-scale into the current zoom object */
    self.zoom.x(self.xScale);
  }
}


/**
 * -------------- Scale Factor Functions --------------
 */
SpectrumChartD3.prototype.numYScalers = function() {
  var self = this;
  
  if( !this.options.scaleBackgroundSecondary || !self.rawData || !self.rawData.spectra )
    return 0;
  
  let nonFore = 0;
  self.rawData.spectra.forEach(function (spectrum) {
    if( spectrum && spectrum.type && spectrum.type !== self.spectrumTypes.FOREGROUND
      && spectrum.yScaleFactor != null && spectrum.yScaleFactor >= 0.0 )
    nonFore += 1;
  });
  
  return nonFore;
}


SpectrumChartD3.prototype.cancelYAxisScalingAction = function() {
  var self = this;
  
  if( !self.rawData || !self.rawData.spectra || self.currentlyAdjustingSpectrumScale === null )
    return;
  
  console.log( 'cancelYAxisScalingAction');
  
  var scale = null;
  for (var i = 0; i < self.rawData.spectra.length; ++i) {
    let spectrum = self.rawData.spectra[i];
    
    if( spectrum.type == self.currentlyAdjustingSpectrumScale ) {
      spectrum.yScaleFactor = spectrum.startingYScaleFactor;
      spectrum.startingYScaleFactor = null;
      self.endYAxisScalingAction()();
      self.redraw()();
      return;
    }
  }
}

SpectrumChartD3.prototype.endYAxisScalingAction = function() {
  var self = this;
  
  return function(){
    if( self.currentlyAdjustingSpectrumScale === null
      || !self.rawData || !self.rawData.spectra )
      return;

    console.log( 'endYAxisScalingAction');
    
    var scale = null;
  
    for( var i = 0; i < self.rawData.spectra.length; ++i ) {
    
      let spectrum = self.rawData.spectra[i];
    
      if( spectrum.type == self.currentlyAdjustingSpectrumScale ) {
        spectrum.sliderText.style( "display", "none" );
        spectrum.sliderToggle.attr("cy", Number(spectrum.sliderRect.attr("y"))
                                          + Number(spectrum.sliderRect.attr("height"))/2);
                                          
        spectrum.sliderRect.attr("stroke-opacity", 0.8).attr("fill-opacity", 0.3);
        spectrum.sliderToggle.attr("stroke-opacity", 0.8).attr("fill-opacity", 0.7);
                                          
        spectrum.startingYScaleFactor = null;
        scale = spectrum.yScaleFactor;
        break;
      }
    }
  
    if( scale !== null ){
      self.WtEmit(self.chart.id, {name: 'yscaled'}, scale, self.currentlyAdjustingSpectrumScale );
      console.log('Emmitted yscaled scale=' + scale + ', type=' + self.currentlyAdjustingSpectrumScale );
    } else {
      console.log('Failed to find scale factor being adjusted');
    }
  
    self.currentlyAdjustingSpectrumScale = null;
  }
}


SpectrumChartD3.prototype.drawScalerBackgroundSecondary = function() {
  var self = this;
  
  //This function called from setData() and handleResize(), so not too often.
  //  (ToDo: it also gets needlessly called occasitonally when zooming - should fix)
  
  //console.log( 'drawScalerBackgroundSecondary' );
  
  //ToDo: - Instead of using spectrum.type to identify which spectrum is being scaled, use spectrum.id (but make sure id is always unique)
  
  const nScalers = self.numYScalers();
  if( nScalers === 0 || self.size.height < 35 ){
    if( self.scalerWidget )
      self.removeSpectrumScaleFactorWidget();
    return;
  }

  if( !self.scalerWidget ){
    self.scalerWidget = d3.select(this.chart).select("svg").append("g")
      .attr("class", "scalerwidget")
      .attr("transform","translate(" + (this.cx - 20*nScalers) + "," + this.padding.topComputed + ")");

    self.scalerWidgetBody = self.scalerWidget.append("g")
      .attr("transform","translate(0,0)");
  }

  //The number of scalers may have changed since we created self.scalerWidget,
  //  so update its position.
  self.scalerWidget
      .attr("transform","translate(" + (this.cx - 20*nScalers) + "," + this.padding.topComputed + ")");
  
  
  self.scalerWidgetBody.selectAll("g").remove();

  function is_touch_device() {
    return 'ontouchstart' in window        /* works on most browsers  */
        || (navigator && navigator.maxTouchPoints);       /* works on IE10/11 and Surface */
  };

  var scalerHeight = self.size.height - 30;
  //var toggleRadius = is_touch_device() ? 10 : 7;  //ToDo: For touch devices if we go to 10 px, then it isnt centered on spectrum.sliderRect, and also it hangs off the screen (or at least would got to very edge.
  var toggleRadius = 7;
  var ypos = 15;

  //Get axis color, text color and spec
  let axiscolor = 'black', txtcolor = 'black';
  const tickElement = document.querySelector('.tick');
  const tickStyle = tickElement ? getComputedStyle(tickElement) : null;
  axiscolor = tickStyle && tickStyle.stroke ? tickStyle.stroke : 'black';
  
  const titleElement = document.querySelector('.xaxistitle');
  const titleStyle = titleElement ? getComputedStyle(titleElement) : null;
  txtcolor = titleStyle && titleStyle.stroke ? titleStyle.stroke : 'black';
  
  
  var scalenum = 0;
  self.rawData.spectra.forEach(function(spectrum,i) {
    var spectrumScaleFactor = spectrum.yScaleFactor;
    var spectrumSelector = 'Spectrum-' + spectrum.id;

    if (i == 0 || spectrum.type === self.spectrumTypes.FOREGROUND)   /* Don't add scaling functionality for foreground */
    return;
      
    if (spectrumScaleFactor != null && spectrumScaleFactor >= 0) {
      scalenum += 1;
      
      let speccolor = spectrum.lineColor ? spectrum.lineColor : 'black';
      
      var spectrumSliderArea = self.scalerWidgetBody.append("g")
        .attr("id", spectrumSelector + "SliderArea")
        .attr("transform","translate(" + 20*(scalenum-1) + "," + ypos + ")");

      spectrum.sliderText = spectrumSliderArea.append("text")
        .attr("x", 0)
        .attr("y", self.size.height-15)
        .attr("text-anchor", "start")
        .attr("fill", txtcolor )
        .style( "display", "none" )
        .text( "" + spectrumScaleFactor.toFixed(3));

      spectrum.sliderRect = spectrumSliderArea.append("rect")
        .attr("class", "scaleraxis")
        .attr("y", 0 /* + (is_touch_device() ? 5 : 0)*/ )
        .attr("x", 8)
        .attr("rx", 5)
        .attr("ry", 5)
        .attr("stroke", axiscolor )
        .attr("stroke-opacity", 0.8)
        .attr("fill", speccolor )
        .attr("fill-opacity", 0.3)
        .attr("width", "4px")
        .attr("height", scalerHeight );
 

      spectrum.sliderToggle = spectrumSliderArea.append("circle")
        .attr("class", "scalertoggle")
        .attr("cx", Number(spectrum.sliderRect.attr("x")) + toggleRadius/2 - 1)
        .attr("cy", Number(spectrum.sliderRect.attr("y")) + scalerHeight/2)
        .attr("r", toggleRadius)
        .attr("stroke", axiscolor )
        .attr("stroke-opacity", 0.8)
        .attr("fill", speccolor )
        .attr("fill-opacity", 0.7)
        .style("cursor", "pointer")
        .on("mousedown", function(){
          self.handleMouseMoveScaleFactorSlider();
          registerKeyboardHandler(self.keydown());
          spectrum.sliderRect.attr("stroke-opacity", 1.0).attr("fill-opacity", 1.0);
          spectrum.sliderToggle.attr("stroke-opacity", 1.0).attr("fill-opacity", 1.0);
          spectrum.startingYScaleFactor = spectrum.yScaleFactor;
          self.currentlyAdjustingSpectrumScale = spectrum.type;
          spectrum.sliderText.style( "display", null )
          d3.event.preventDefault();
          d3.event.stopPropagation();
        })
        .on("mousemove", self.handleMouseMoveScaleFactorSlider())
        .on("mouseup", self.endYAxisScalingAction() )
        .on("touchstart", function(){
          self.handleMouseMoveScaleFactorSlider();
          registerKeyboardHandler(self.keydown());
          spectrum.sliderRect.attr("stroke-opacity", 1.0).attr("fill-opacity", 1.0);
          spectrum.sliderToggle.attr("stroke-opacity", 1.0).attr("fill-opacity", 1.0);
          spectrum.startingYScaleFactor = spectrum.yScaleFactor;
          self.currentlyAdjustingSpectrumScale = spectrum.type;
          spectrum.sliderText.style( "display", null )
        })
        .on("touchmove", self.handleMouseMoveScaleFactorSlider())
        .on("touchend", self.endYAxisScalingAction() );
    }
  });
}

SpectrumChartD3.prototype.removeSpectrumScaleFactorWidget = function() {
  var self = this;

  if (self.scalerWidget) {
    self.scalerWidget.remove();
    self.scalerWidget = null;
    self.scalerWidgetBody = null;
    
    if( self.rawData && self.rawData.spectra ) {
      self.rawData.spectra.forEach( function(spectrum,i) {
        spectrum.sliderText = null;
        spectrum.sliderRect = null;
        spectrum.sliderToggle = null;
      } );
    }
  }
}


SpectrumChartD3.prototype.setShowSpectrumScaleFactorWidget = function(d) {
  this.options.scaleBackgroundSecondary = d;
  this.handleResize( false );
}

SpectrumChartD3.prototype.handleMouseMoveScaleFactorSlider = function() {
  var self = this;

  function needsDecimal(num) {
    return num % 1 != 0;
  }

  /* Here is a modified, slightly more efficient version of redraw 
    specific to changing the scale factors for spectrums. 
  */
  function scaleFactorChangeRedraw(spectrum, linei) {
    self.updateLegend();
    self.rebinSpectrum(spectrum, linei);
    self.do_rebin();
    self.rebinForBackgroundSubtract();
    self.setYAxisDomain();
    self.drawYTicks();
    self.update();
    self.drawPeaks();
  }

  return function() {
    if (!self.rawData || !self.rawData.spectra || !self.rawData.spectra.length )
      return;
    if (!self.currentlyAdjustingSpectrumScale)
      return;

    /* Check for the which corresponding spectrum line is the background */
    var linei = null;
    var spectrum = null;
    for (var i = 0; i < self.rawData.spectra.length; ++i) {
      if (self.rawData.spectra[i].type == self.currentlyAdjustingSpectrumScale) {
        linei = i;
        spectrum = self.rawData.spectra[i];
        break;
      }
    }

    d3.event.preventDefault();
    d3.event.stopPropagation();

    if (linei === null || spectrum === null)
      return;

    d3.select(document.body).style("cursor", "pointer");

    var m = d3.mouse(spectrum.sliderRect[0][0]);
    if( !m ){
      //ToDo: test that this works, and is necassary on touch devices!
      //console.log( 'Using touches!' );
      m = d3.touches(spectrum.sliderRect[0][0]);
      if( m.length !== 1 )
        return;
      m = m[0];
    }
    
    
    let scalerHeight = Number(spectrum.sliderRect.attr("height"));
    let rad = Number(spectrum.sliderToggle.attr("r"));
    let newTogglePos = Math.min(Math.max(0,m[1]+rad/2),scalerHeight);
    
    let fracOnScale = 1.0 - newTogglePos/scalerHeight;
    
    
    var sf = 1.0;
    if( self.options.yscale === "log" ) {
      //[0.001*scale, 1000*scale]
      sf = Math.exp( Math.log(0.001) + fracOnScale*(Math.log(1000) - Math.log(0.001)) );
    } else if( self.options.yscale === "sqrt" ) {
      //ToDo: make so sf will go from 0.01 to 100 with 0.5 giving 1
      sf = 1.38734467428311845572*(Math.exp(fracOnScale) - 1) + 0.1;
    } else {
      //ToDo: make so when fracOnScale is zero, want scale=0.1, when 0.5 want scale=1.0, when 1.0 want scale=10
      //from 0.1 to 1.9
      //sf = 1.8*fracOnScale + 0.1;
      sf = 1.38734467428311845572*(Math.exp(fracOnScale) - 1) + 0.1;
    }
    
    var spectrumScaleFactor = sf*spectrum.startingYScaleFactor;
    
    spectrum.sliderToggle.attr("cy", newTogglePos );
    spectrum.sliderText.text( (needsDecimal(spectrumScaleFactor) ? spectrumScaleFactor.toFixed(3) : spectrumScaleFactor.toFixed()));
    spectrum.yScaleFactor = spectrumScaleFactor;
    
    // If we are using background subtract, we have to redraw the entire chart if we update the scale factors
    if (self.options.backgroundSubtract) self.redraw()();
    else scaleFactorChangeRedraw(spectrum, linei);


    /* Update the slider chart if needed */
    if (self["sliderLine"+linei]) {
      var origdomain = self.xScale.domain();
      var origdomainrange = self.xScale.range();
      var origrange = self.yScale.domain();
      var bounds = self.min_max_x_values();
      var maxX = bounds[1];
      var minX = bounds[0];

      /* Change the x and y-axis domain to the full range (for slider lines) */
      self.xScale.domain([minX, maxX]);
      self.xScale.range([0, self.size.sliderChartWidth]);
      self.do_rebin();
      self.rebinForBackgroundSubtract();
      self.yScale.domain(self.getYAxisDomain());

      self.rawData.spectra.forEach(function(spec, speci) {
        if (self["sliderLine"+speci])
          self["sliderLine"+speci].attr("d", self["line"+speci](spec[self.options.backgroundSubtract ? 'bgsubtractpoints' : 'points']));
      })
      

      /* Restore the original x and y-axis domain */
      self.xScale.domain(origdomain);
      self.xScale.range(origdomainrange);
      self.do_rebin();
      self.rebinForBackgroundSubtract();
      self.yScale.domain(origrange);
    }
  }
}


SpectrumChartD3.prototype.offset_integral = function(roi,x0,x1){
  if( roi.type === 'NoOffset' || x0===x1 )
    return 0.0;
  
  if( roi.type === 'External' ){
    //console.log( roi );

    let energies = roi.continuumEnergies;
    let counts = roi.continuumCounts;

    if( !energies || !energies.length || !counts || !counts.length ){
      console.warn( 'External continuum does not have continuumEnergies or continuumCounts' );
      return 0.0;
    }

    let bisector = d3.bisector(function(d){return d;});
    let cstartind = bisector.left( energies, Math.max(roi.lowerEnergy,x0) );
    let cendind = bisector.right( energies, Math.min(roi.upperEnergy,x1) );
    
    if( cstartind >= (energies.length-1) )
      return 0.0;  //shouldnt ever happen
    if( cendind >= (energies.length-1) )
      cendind = cendind - 1;

    if( cstartind > 0 && energies[cstartind] > x0 )
      cstartind = cstartind - 1;
    if( cendind > 0 && energies[cendind] > x1 )
      cendind = cendind - 1;

    if( cstartind === cendind ){
      return counts[cstartind] * (x1-x0) / (energies[cstartind+1] - energies[cstartind]);
    }

    //figure out fraction of first bin
    let frac_first = (energies[cstartind+1] - x0) / (energies[cstartind+1] - energies[cstartind]);
    let frac_last = 1.0 - (energies[cendind+1] - x1) / (energies[cendind+1] - energies[cendind]);
      
    //console.log( 'x0=' + x0 + ', cstartind=' + cstartind + ', energy={' + energies[cstartind] + ',' + energies[cstartind+1] + '}, frac_first=' + frac_first );
    //console.log( 'x1=' + x1 + ', cendind=' + cendind + ', energy={' + energies[cendind] + ',' + energies[cendind+1] + '}, frac_last=' + frac_last);

    let sum = frac_first*counts[cstartind] + frac_last*counts[cendind];
    for( let i = cstartind+1; i < cendind; ++i )
      sum += counts[i];
    return sum;
  }//if( roi.type === 'External' )

  x0 -= roi.referenceEnergy; x1 -= roi.referenceEnergy;
  var answer = 0.0;
  for( var i = 0; i < roi.coeffs.length; ++i )
    answer += (roi.coeffs[i]/(i+1)) * (Math.pow(x1,i+1) - Math.pow(x0,i+1));
  return Math.max( answer, 0.0 );
}

/**
 * -------------- Peak ROI/Label Rendering Functions --------------
 */
SpectrumChartD3.prototype.drawPeaks = function() {
  var self = this;

  self.peakVis.selectAll("*").remove();
  self.peakPaths = [];
  self.labelinfo = null;
  
  
  if( !this.rawData || !this.rawData.spectra ) 
    return;

  var minx = self.xScale.domain()[0], maxx = self.xScale.domain()[1];

  let labelinfo = [];
  let showlabels = (self.options.showUserLabels || self.options.showPeakLabels || self.options.showNuclideNames);
  
  
  /* Returns an array of paths.  
     - The first path will be an underline of entire ROI
     - The next roi.peaks.length entries are the fills for each of the peaks
     - The next roi.peaks.length entries are the path of the peak, that sits on the ROI
   */
  function roiPath(roi,points,bgsubtractpoints,scaleFactor,background){
    var paths = [];
    var labels = showlabels ? [] : null;
    var bisector = d3.bisector(function(d){return d.x;});
    
    let roiLB = Math.max(roi.lowerEnergy,minx);
    let roiUB = Math.min(roi.upperEnergy,maxx);
    
    var xstartind = bisector.left( points, roiLB );
    var xendind = bisector.right( points, roiUB );

    // Boolean to signify whether to subtract points from background
    const useBackgroundSubtract = self.options.backgroundSubtract && background;

    if( xstartind >= (points.length-2) )
      return { paths: paths };
      
    if( xendind >= (points.length-2) )
      xendind = points.length - 2;

    //console.log( 'roi.lowerEnergy=', roi.lowerEnergy, ', xstartind=', points[xstartind] );
    //console.log( 'roi.upperEnergy=', roi.upperEnergy, ', xendind=', points[xendind] );
      
    /*The continuum values used for the first and last bin of the ROI are fudged */
    /*  for now...  To be fixed */

    /*XXX - Need to check continuum type!!! */

    var thisy = null, thisx = null, m, s, peak_area, cont_area;
    
    //Need to go thorugh and get min/max, in px of each ROI, and save it somehome
    //  so we can draw the line in only the ROI's y-domain
    //var minyval_px = self.size.height
    //    , maxyval_py = 0;
    var firsty = self.offset_integral( roi, points[xstartind-(xstartind?1:0)].x, points[xstartind+(xstartind?0:1)].x ) * scaleFactor;
    
    // Background Subtract - Subtract the initial y-value with the corresponding background point
    if (useBackgroundSubtract) {
      var bi = bisector.left(background.points, points[xstartind-(xstartind?1:0)].x);
      firsty -= background.points[bi] ? background.points[bi].y : 0;
    }
    
    //paths[0] = "M" + self.xScale(points[xstartind].x) + "," + self.yScale(firsty) + " L";
    paths[0] = "M" + self.xScale(roiLB) + "," + self.yScale(firsty) + " L";
    
    for( var j = 0; j < 2*roi.peaks.length; ++j )
      paths[j+1] = "";
      
    //Go from left to right and create lower path for each of the outlines that sit on the continuum
    for( var i = xstartind; i < xendind; ++i ) {
      thisx = ((i===xstartind) ? roiLB : ((i===(xendind-1)) ? roiUB : (0.5*(points[i].x + points[i+1].x))));
      thisy = self.offset_integral( roi, points[i].x, points[i+1].x ) * scaleFactor;
      
      // Background Subtract - Subtract the current y-value with the corresponding background point
      if (useBackgroundSubtract) {
        var bi = bisector.left(background.points, points[i].x);
        thisy -= background.points[bi] ? background.points[bi].y : 0; 
      }

      paths[0] += " " + self.xScale(thisx) + "," + self.yScale(thisy);
      
      for( let j = 0; j < roi.peaks.length; ++j ) {
        m = roi.peaks[j].Centroid[0];
        s = roi.peaks[j].Width[0];
        
        if( labels && m>=points[i].x && m<points[i+1].x ) {
          //This misses any peaks with means not on the chart
          if( !labels[j] )
            labels[j] = {};
          //ToDo: optimize what we actually need in these objects
          labels[j].xindex = i;
          labels[j].roiPeakIndex = j;
          labels[j].roi = roi;
          labels[j].peak = roi.peaks[j];
          labels[j].centroidXPx = self.xScale(m);
          labels[j].centroidMinYPx = self.yScale(thisy);
          labels[j].energy = m;
          labels[j].userLabel = roi.peaks[j].userLabel;
        }//if( the centroid of this peak is in this bin )
        
        if( roi.peaks.length===1 || (thisx > (m - 5*s) && thisx < (m+5*s)) ){
          if( !paths[j+1].length ){
            paths[j+1+roi.peaks.length] = "M" + self.xScale(thisx) + "," + self.yScale(thisy) + " L";
          }else{
            paths[j+1+roi.peaks.length] += " " + self.xScale(thisx) + "," + self.yScale(thisy);
          }
        }
      }
    }//for( var i = xstartind; i < xendind; ++i )

    function erf(x) {
      /* http://stackoverflow.com/questions/14846767/std-normal-cdf-normal-cdf-or-error-function
         Error is less than 1.5 * 10-7 for all inputs
         (from Handbook of Mathematical Functions)
       */
      const sign = (x >= 0) ? 1 : -1; /* save the sign of x */
      x = Math.abs(x);
      const a1 = 0.254829592, a2 = -0.284496736, a3 = 1.421413741, a4 = -1.453152027,
          a5 = 1.061405429, p  = 0.3275911;
      const t = 1.0/(1.0 + p*x);
      const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);
      return sign * y; /* erf(-x) = -erf(x); */
    }

    function gaus_integral( peak, x0, x1 ) {
      var peak_mean = peak.Centroid[0], peak_sigma = peak.Width[0], peak_amplitude = peak.Amplitude[0];
         /*peak.LandauAmplitude, peak.LandauMode, peak.LandauSigma, */
      var sqrt2 = 1.414213562373095;
      var erflowarg = (x0-peak_mean)/(sqrt2*peak_sigma);
      var erfhigharg = (x1-peak_mean)/(sqrt2*peak_sigma);
      return peak_amplitude * 0.5 * (erf(erfhigharg) - erf(erflowarg));
    };

    var bisector = d3.bisector(function(d){return d.x;});

    var peakamplitudes = [];  //The peak amplitudes for each bin

    var leftMostLineValue = [];

    var minypx = self.size.height, maxypx = 0;
    
    //Go from right to left drawing the peak lines that sit on the continuum.
    //  we will also 
    for( var xindex = xendind - 1; xindex >= xstartind; --xindex ) {
      peakamplitudes[xindex] = [];
      peak_area = 0.0;
      //thisx = 0.5*(points[xindex].x + points[xindex+1].x);
      thisx = ((xindex===xstartind) ? roiLB : ((xindex===(xendind-1)) ? roiUB : (0.5*(points[xindex].x + points[xindex+1].x))));
      
      
      cont_area = self.offset_integral( roi, points[xindex].x, points[xindex+1].x ) * scaleFactor;

      // Background Subtract - Subtract the current y-value with the corresponding background point
      if( useBackgroundSubtract ) 
        cont_area -= background.points[bisector.left(background.points, points[xindex].x)].y;

      peakamplitudes[xindex][0] = cont_area;
      peakamplitudes[xindex][1] = thisx;

      roi.peaks.forEach( function(peak,peakn){
        const ispeakcenter = (labels && labels[peakn] && labels[peakn].xindex===xindex);
        
        if( peak.type === 'GaussianDefined' ){
          let area = gaus_integral( peak, points[xindex].x, points[xindex+1].x ) * scaleFactor;
          peak_area += area;

          if( peak.skewType !== 'NoSkew' )
            console.log( 'Need to implement peak skew type ' + peak.skewType );

          m = peak.Centroid[0];
          s = peak.Width[0];
          
          if( roi.peaks.length==1 || (thisx > (m - 5*s) && thisx < (m+5*s)) ){
            peakamplitudes[xindex][peakn+2] = area;
            let yvalpx = self.yScale(cont_area + area);
            minypx = Math.min(minypx,yvalpx);
            maxypx = Math.max(maxypx,yvalpx);
            if( ispeakcenter )
              labels[peakn].centroidMaxYPx = yvalpx;
            paths[peakn+1+roi.peaks.length] += " " + self.xScale(thisx) + "," + yvalpx;
            leftMostLineValue[peakn] = {x : thisx, y: cont_area};
          }else{
            peakamplitudes[xindex][peakn+2] = 0.0;
          }
        } else if( peak.type === 'DataDefined' ) {
          let area = points[xindex].y - cont_area;
          peakamplitudes[xindex][peakn+2] = (area > 0 ? area : 0);
          let yvalpx = self.yScale(cont_area + (area >= 0 ? area : 0.0));
          minypx = Math.min(minypx,yvalpx);
          maxypx = Math.max(maxypx,yvalpx);
          if( ispeakcenter && labels[peakn] )
            labels[peakn].centroidMaxYPx = yvalpx;
          paths[peakn+1+roi.peaks.length] += " " + self.xScale(thisx) + "," + yvalpx;
          leftMostLineValue[peakn] = {x : thisx, y: cont_area};
        } else {
          console.log( 'Need to implement peak.type==' + peak.type );
          return;
        }
      });
    }//for( go right to left over 'xindex' drawing peak outlines )

    
    //Make sure the peak line top connects with the continuum
    for( var j = 0; j < roi.peaks.length; ++j ) {
      var pathnum = j+1+roi.peaks.length;
      if( leftMostLineValue[j] && paths[pathnum] && paths[pathnum].length )
        paths[pathnum] += " " + self.xScale(leftMostLineValue[j].x) + "," + self.yScale(leftMostLineValue[j].y);
    }
    

    var leftMostFillValue = [];
    //go from left to right, drawing fill area bottom
    peakamplitudes.forEach( function(peakamps,xindex){
      var cont = peakamps[0];
      var thisx = peakamps[1];

      peakamps.forEach( function( peakamp, peakindex ){
        if( peakindex < 2 )
          return;
        var peaknum = (peakindex - 2);
        var peak = roi.peaks[peaknum];
        var m = peak.Centroid[0];
        var s = peak.Width[0];
        if( roi.peaks.length>1 && (thisx < (m - 5*s) || thisx > (m+5*s)) )
          return;
        
        var thisy = cont;
        for( var j = 2; j < peakindex; ++j )
          thisy += peakamps[j];
          
        let yvalpx = self.yScale(thisy);
        let xvalpx = self.xScale(thisx);
        minypx = Math.min(minypx,yvalpx);
        maxypx = Math.max(maxypx,yvalpx);
          
        if( !paths[peaknum+1].length ){
          leftMostFillValue[peaknum] = { x: xvalpx, y: yvalpx };
          paths[peaknum+1] = "M" + xvalpx + "," + yvalpx + " L";
        }else{
          paths[peaknum+1] += " " + xvalpx + "," + yvalpx;
        }
      } );
    });

    //console.log( 'minypx=' + minypx + ', maxypx=' + maxypx + ' height=' + self.size.height );
    
    //go right to left and draw the fill areas top
    peakamplitudes.reverse().forEach( function(peakamps,xindex){
      var cont = peakamps[0];
      var thisx = peakamps[1];
      
      peakamps.forEach( function( peakamp, peakindex ){
        if( peakindex < 2 )
          return;

        var peaknum = (peakindex - 2);
        var peak = roi.peaks[peaknum];
        var m = peak.Centroid[0];
        var s = peak.Width[0];
        if( roi.peaks.length>1 && (thisx < (m - 5*s) || thisx > (m+5*s)) )
          return;
        
        var thisy = cont;
        for( var j = 2; j <= peakindex; ++j )
          thisy += peakamps[j];

        paths[peaknum+1] += " " + self.xScale(thisx) + "," + self.yScale(thisy);
      } );
    });

    for( var peaknum = 0; peaknum < roi.peaks.length; ++peaknum ){
      if( leftMostFillValue[peaknum] && paths[peaknum+1].length )
        paths[peaknum+1] += " " + leftMostFillValue[peaknum].x + "," + leftMostFillValue[peaknum].y;
    }
    
    //console.log( 'roiPath labels=', labels );
    
    return {paths: paths, yRangePx: [minypx,maxypx], labelinfo: labels };
  }/*function roiPath(roi) */

  function draw_roi(roi,specindex,spectrum) {
    if( roi.type !== 'NoOffset' && roi.type !== 'Constant'
        && roi.type !== 'Linear' && roi.type !== 'Quadratic'
        && roi.type !== 'Quardratic' //vestigual, can be deleted in the future.
        && roi.type !== 'Cubic' && roi.type !== 'External' ){
      console.log( 'unrecognized roi.type: ' + roi.type );
      return;
    }

    if( roi.lowerEnergy > maxx || roi.upperEnergy < minx )
      return;

    if (!spectrum) {
      console.log("No spectrum specified to draw peaks");
      return;
    }
    
    if( self.yScale.domain()[0] === self.yScale.domain()[1] ){
      console.log( 'Y-domain not valid; not drawing ROI' );
      return;
    }

    let scaleFactor = spectrum.type !== self.spectrumTypes.FOREGROUND ? spectrum.yScaleFactor * 1.0 : 1.0;
    if (typeof scaleFactor === 'undefined' || scaleFactor === null) scaleFactor = 1.0;

    var pathsAndRange = roiPath( roi, spectrum.points, spectrum.bgsubtractpoints, scaleFactor, self.getSpectrumByID(spectrum.backgroundID) );

    if( pathsAndRange.labelinfo )
      Array.prototype.push.apply(labelinfo,pathsAndRange.labelinfo);
    
    /* Draw label, set fill colors */
    pathsAndRange.paths.forEach( function(p,num){

      /* - The first path will be an underline of entire ROI
         - The next roi.peaks.length entries are the fills for each of the peaks
         - The next roi.peaks.length entries are the path of the peak, that sits on the ROI
      */
      if( num === 0 )
        return;

      //If only a single peak in a ROI, we will use the same path for outline and fill
      if( roi.peaks.length==1 && num > roi.peaks.length )
        return;
      
      let isOutline = ((num > (roi.peaks.length)) || (roi.peaks.length==1));
      let isFill  = (num <= (roi.peaks.length));

      var path = self.peakVis.append("path").attr("d", p );


      function onRightClickOnPeak() {
        console.log("Emit RIGHT CLICK (ON PEAK) signal. (Peak roi = ", roi, ")");
      }

      var peakind = (num-1) % roi.peaks.length;
      var peak = roi.peaks[peakind];
      var peakColor = peak && peak.lineColor && peak.lineColor.length ? peak.lineColor : spectrum.peakColor;

      self.peakPaths.push({
            path: path,
            paths: pathsAndRange.paths,
            roi: roi,
            lowerEnergy: roi.lowerEnergy,
            upperEnergy: roi.upperEnergy,
            yRangePx: pathsAndRange.yRangePx,
            color: peakColor,
            isOutline: isOutline,
            isFill: isFill
      });

      path/* .attr("class", "peak") */
          /* .attr("class", "spectrum-peak-" + specindex) */
          .attr("stroke-width", 1)
          .attr("stroke", peakColor )
          ;
            
      path.attr("fill-opacity", ((isOutline && !isFill) ? 0.0 : 0.6) )
          .attr("data-energy", ((peak && peak.Centroid) ? peak.Centroid[0].toFixed(2) : 0) );

      if( isFill ){
        path.style("fill", peakColor )
            .attr("class", "peakFill" )
      } else if( isOutline ) {
        path.attr("class", "peakOutline" )
      }
      
      if( isOutline ){
        path.on("mouseover", function(){ self.handleMouseOverPeak(this); } )
            .on("mousemove", self.handleMouseMovePeak())
            .on("touchend", function(){ self.handleMouseOverPeak(this);} )
            .on("mouseout", function(d, peak) { self.handleMouseOutPeak(this, peak, pathsAndRange.paths); } );
      }
      

      /* For right-clicking on a peak */
      path.on("contextmenu", onRightClickOnPeak);
    });//pathsAndRange.paths.forEach( function(p,num){

    
    if( pathsAndRange.paths.length > 0 && roi.peaks.length > 1 ){
      //Draw the continuum line for multiple peak ROIs
      var path = self.peakVis.append("path").attr("d", pathsAndRange.paths[0] );  //ToDo: is there a better way to draw a SVG path?
      path/*.attr("class", "spectrum-peak-" + specindex)*/
          .attr("stroke-width",1)
          .attr("fill-opacity",0)
          .attr("stroke", spectrum.peakColor );
    }
  };//function draw_roi(roi,specindex,spectrum)

  for (let i = 0; i < this.rawData.spectra.length; i++) {
    const spectrum = this.rawData.spectra[i];
    
    if ((spectrum.type === self.spectrumTypes.FOREGROUND && !this.options.drawPeaksFor.FOREGROUND))
      continue;
    if ((spectrum.type === self.spectrumTypes.BACKGROUND && (!this.options.drawPeaksFor.BACKGROUND || this.options.backgroundSubtract)))
      continue;
    if ((spectrum.type === self.spectrumTypes.SECONDARY && !this.options.drawPeaksFor.SECONDARY))
      continue;

    const peaks = spectrum.peaks;
    if( peaks ){
      peaks.forEach( function(roi){
        //We test for self.roiBeingDrugUpdate below, even if self.roiIsBeingDragged is true, to make sure the server has
        //  actually returned a updated ROI, and if it hasnt, we'll draw the original ROI.
        //  This prevents to ROI disapearing after the user clicks down, but before they have moved the mouse.
        if( self.roiIsBeingDragged && self.roiBeingDrugUpdate && roi == self.roiBeingDragged.roi )
          draw_roi(self.roiBeingDrugUpdate,i,spectrum);
        else
          draw_roi(roi,i,spectrum);
      });
    }//if( this.rawData.spectra[i].peaks )
    
    if( self.fittingPeak && self.roiBeingDrugUpdate && (this.rawData.spectra[i].type === self.spectrumTypes.FOREGROUND) )
      draw_roi(self.roiBeingDrugUpdate,i,spectrum);
  }
  
  self.drawPeakLabels( labelinfo );
}

SpectrumChartD3.prototype.drawPeakLabels = function( labelinfos ) {
  var self = this;
  
  //console.log( "labelinfos=", labelinfos );
  
  /*
   ToDo items w.r.t. labels:
     - Peak labels can overlap peaks - should be fixed.
     - Add user labels not associated with peaks.
     - Add right click menu to edit label (both for non-peak labels, and normal labels)
   */
  

  if( !labelinfos || labelinfos.length===0 )
    return;
    
  if( !self.options.showUserLabels && !self.options.showPeakLabels && !self.options.showNuclideNames )
    return null;
    
  let chart = self.peakVis;
  let chartBox = d3.select("#chartarea"+self.chart.id)[0][0].getBBox();    /* box coordinates for the chart area */
  
  // Don't draw peak label if chart isn't set up yet
  if( !chartBox.width || !chartBox.height )
    return null;
  
  const chartw = chartBox.width;
  const charth = chartBox.height;
  
  const tickElement = document.querySelector('.tick');
  const tickStyle = tickElement ? getComputedStyle(tickElement) : null;
  const axiscolor = tickStyle && tickStyle.stroke ? tickStyle.stroke : 'black';
  
  
  /*
   labelinfos is an array of objects that look like:
   {
   centroidMaxYPx: 33.6
   centroidMinYPx: 43.0
   centroidXPx: 111.4
   energy: 244.162
   peak: {type: "GaussianDefined", skewType: "NoSkew", Centroid: Array(3), Width: Array(3), Amplitude: Array(3), …}
   roi: {type: "Linear", lowerEnergy: 220.469, upperEnergy: 271.636, referenceEnergy: 220.469, coeffs: Array(2), …}
   roiPeakIndex: 0
   userLabel: undefined
   }
   */
  
  let drawnlabels = [];
  
  for( let index = 0; index < labelinfos.length; ++index ){
    let info = labelinfos[index];
    if( !info || typeof(info)==='undefined' || !info.peak )
      continue;
    
    let nuclide = info.peak.nuclide;
    if( !nuclide )
      nuclide = info.peak.xray
    if( !nuclide )
      nuclide = info.peak.reaction
  
    //If we wont draw any text, just return now
    //  (ToDo: I think this case has already been filetered out, check, and if so remove next lines)
    if( !(self.options.showUserLabels && info.userLabel)
        && !self.options.showPeakLabels
        && !(self.options.showNuclideNames && nuclide) ){
      continue;
    }
    
    let peak_x = info.centroidXPx;
    let peak_ly = info.centroidMinYPx;
    let peak_uy = info.centroidMaxYPx;
    
    
    //This next check doesnt appear to be necassary anymore.
    if( peak_uy===null || Number.isNaN(peak_uy) || typeof(peak_uy)==='undefined'
       || peak_ly===null || Number.isNaN(peak_ly) || typeof(peak_ly)==='undefined' )
    {
      console.log( 'Got peak_uy=' + peak_uy + ', peak_ly=' + peak_ly + ' for energy ' + info.energy, info );
      continue;
    }
    
    
    let peakEnergy = info.energy.toFixed(2) + " keV";
    
    var label, userLabel, peakEnergyLabel, nuclideNameLabel;
    
    /* Main label DOM */
    label = chart.append("text");
    label.attr('class', 'peaklabel')
    .attr("text-anchor", "start")
    .attr("y", peak_uy - 10 )
    .attr("x", peak_x)           //Doesnt seem to be needed since we are using all <tspan>s
    .attr("energy", peakEnergy)  //Dont think this is needed
    .attr("fill", axiscolor )
    .attr("data-labelindex", index)  //Is there a better way to associate the labelinfos object with this label?  Probably, but whatever for now.
    .attr("data-peak-energy", info.energy.toFixed(2) )
    .attr("data-peak-x-px", peak_x.toFixed(1) )
    .attr("data-peak-lower-y-px", peak_ly.toFixed(1) )
    .attr("data-peak-upper-y-px", peak_uy.toFixed(1) )
    ;
    
    if( self.options.showUserLabels && info.userLabel ){
      /* T-span element for the user label */
      /* Gets priority for top-most text in label */
      userLabel = label.append("tspan");
      userLabel.attr("class", "userLabel")
      .attr("dy", 0)
      .attr("x", peak_x)
      .text(info.userLabel);
    }
    
    if( self.options.showPeakLabels ) {
      /* T-span element for the peak label */
      /* Gets second in priority for top-most text in label */
      peakEnergyLabel = label.append("tspan");
      peakEnergyLabel.attr("class", "peakEnergyLabel")
      .attr("dy", userLabel ?  "1em" : 0)   /* If user label is not present, then this is the top-most element */
      .attr("x", peak_x)
      .text(peakEnergy);
    }
    
    if( self.options.showNuclideNames && nuclide ) {
      /* T-span element for nuclide label */
      /* Third in priority for top-most text in label */
      nuclideNameLabel = label.append("tspan");
      nuclideNameLabel.attr("class", "nuclideLabel")
      .attr("dy", self.options.showUserLabels && self.options.showPeakLabels ? "1em" : self.options.showUserLabels || self.options.showPeakLabels ?  "1em" : 0)
      .attr("x", peak_x)
      .text(nuclide.name);
      
      
      /* Nuclide energy label displayed only if nuclide name labels are displayed! */
      //console.log( 'nuclide: ', nuclide );
      if( self.options.showNuclideEnergies )
        nuclideNameLabel.text( nuclide.name + ", " + nuclide.energy.toFixed(2).toString() + " keV"
                               + (nuclide.type ? " " + nuclide.type : "") );
    }//if( show nuclide name and we have a nuclide )
    

    // Add handlers to make text bold when you mouse over the label.
    label.on("mouseover", function(){ self.highlightLabel(this,false); } )
         .on("mouseout",  function(){ self.unHighlightLabel(true); } );
    
    if( self.isTouchDevice() )
    label.on("touchstart", function(){ self.highlightLabel(this,false); } );

    
    //Reposition label niavely.
    const lbb = label.node().getBBox();
    const labelh = Math.max(lbb.height,8);
    const labelw = Math.max(lbb.width,10);
    
    //ToDo: if( (peak_uy - 0.5*labelh) < 0 ), then try moving left or right to avoid overlapping with the peak.
    let labely = Math.max( 2+0.5*labelh, peak_uy - 0.5*labelh - 10 );
    let labelx = Math.min( Math.max(2, peak_x-0.5*labelw+5), chartw-labelw-2 );
    
    label.attr("y", labely ).attr("x", labelx );
    label.selectAll("tspan").each(function(d,i){ d3.select(this).attr("x", labelx);});
    
    //Dont bother doing overlap checking for left-most peak.
    if( drawnlabels.length === 0 ){
      drawnlabels.push( label );
      continue;
    }
    
    //Check for overlaps between two BBoxs.
    const xoverlap = function(rect1,rect2){
      return Math.max(0, Math.min(rect1.x+rect1.width, rect2.x+rect2.width) - Math.max(rect1.x, rect2.x));
    };
    
    const yoverlap = function(rect1,rect2){
      return Math.max(0, Math.min(rect1.y+rect1.height, rect2.y+rect2.height) - Math.max(rect1.y, rect2.y));
    };
    
    // ToDo: implement checking for text overlapping peak areas...
    const checkoverlap = function(rect1,rect2){
      //overlapArea = xoverlap() * yoverlap();
      return ((xoverlap(rect1,rect2) > 0) && (yoverlap(rect1,rect2) > 0))
    };//checkoverlap
    
    const origy = labely;
    const origx = labelx;
    
    //First, lets try making the label go higher until we either have no collisions, or we reach the top
    let reachedTop = false;
    for( let otherindex = 0; !reachedTop && otherindex < drawnlabels.length; ++otherindex ){
      let otherlabel = drawnlabels[otherindex];
      let othernode = otherlabel.node();
      
      const leftw = othernode.getBBox().width;
      
      let x_overlap = xoverlap(label.node().getBBox(),otherlabel.node().getBBox()),
          y_overlap = yoverlap(label.node().getBBox(),otherlabel.node().getBBox());
      
      if( x_overlap > 0 && y_overlap > 0  ){
        let newy = otherlabel.node().getBBox().y - 0.5*labelh - 2;
        if( newy > labely )  //Make sure we only move the label up, so the loop will be garunteed to terminate
          newy = labely - 0.5*labelh;
         
        reachedTop = (newy < (2+0.5*labelh));
       
        if( !reachedTop ){
          labely = newy;
          label.attr("y", labely );
          
          //Now we have to start back over and make sure we havent started overlapping
          //  with any peaks before 'otherindex'.
          otherindex = -1;
          continue;
        }
      }//if( x_overlap > 0 && y_overlap > 0  )
    }//for( let otherindex = 0; otherindex < drawnlabels.length; ++otherindex )
    
    //If we reached the top of the chart, lets reset our height, and try a
    //  different approach
    if( reachedTop )
      label.attr("y", origy );
    
    //If reachedTop is true, then we still have an overlap
    let haveOverlap = reachedTop;
    
    //Lets try moving the overlapping label to the left, left, up to 50% of its width
    //  (from its original x), but only if this movement wont also cause an overlap.
    if( haveOverlap ){
      haveOverlap = false;
      for( let otherindex = 0; !haveOverlap && otherindex < drawnlabels.length; ++otherindex ){
        let otherlabel = drawnlabels[otherindex];
        if( checkoverlap(label.node().getBBox(),otherlabel.node().getBBox()) ){
          haveOverlap = true;
          const x_overlap = xoverlap(label.node().getBBox(),otherlabel.node().getBBox());
          let otherinfo = labelinfos[parseInt(otherlabel.attr('data-labelindex'))];
          let otherPeakXpx = otherinfo.centroidXPx;
          const otherWidth = otherlabel.node().getBBox().width;
          const otherNominalX = Math.min( Math.max(2, otherPeakXpx-0.5*otherWidth+5), chartw-otherWidth-2 );
          const otherCurrentX = parseFloat(otherlabel.attr("x"));
          const newOtherX = otherCurrentX - x_overlap - 2;
          if( (newOtherX > (2+0.5*otherWidth)) && (newOtherX >= (otherPeakXpx-otherWidth-10)) ){
            haveOverlap = false;
            
            otherlabel.attr("x", newOtherX );
            otherlabel.selectAll("tspan").each(function(d,i){ d3.select(this).attr("x", newOtherX);});
            
            for( let testindex = 0; !haveOverlap && testindex < drawnlabels.length; ++testindex ){
              if( testindex !== otherindex )
                haveOverlap = checkoverlap(otherlabel.node().getBBox(),drawnlabels[testindex].node().getBBox());
            }
            
            if( haveOverlap ){
              // Move otherlabel back to its original position; haveOverlap being true will stop the loop over otherindex
              otherlabel.attr("x", otherCurrentX );
              otherlabel.selectAll("tspan").each(function(d,i){ d3.select(this).attr("x", otherCurrentX);});
              //console.log( 'For collision with ' + label.attr("energy") + ' couldnt fix by moving '
              //             + otherlabel.attr("energy") + ' to left by ' + x_overlap + 'px');
            } else {
              //console.log( 'Did fix collision between ' + label.attr("energy") + ' and '
              //             + otherlabel.attr("energy") + ' by moving to left by ' + x_overlap + 'px');
            }
          }//if( moving the label to the left enough is a possibility )
        }//if( overlap )
      }//for( let otherindex = 0; !haveOverlap && otherindex < drawnlabels.length; ++otherindex )
    } else {
      if( origy != label.attr("y") ){
        //We did adjust peak label height
        //ToDo: see if peak immediately to the left is higher or lower than this one, and see if
        //      we can make sure the relative label heights are lower/higher to coorespond by possibly
        //      doing doing a swap of y-coordinates, and then checking if this caused any overlaps.
      }
    }//if( moving label up didnt work ) / else
    
    
    //Try moving this label to the right, by up to 50% of its width, but only if this doesnt cause it to go over the next peak
    if( haveOverlap ){
      haveOverlap = false;
      
      let maxxpx = Math.min( peak_x+0.5*labelw+5, chartw-labelw-2 );
      if( (index+1) < labelinfos.length )
        maxxpx = Math.min( maxxpx, labelinfos[index+1].centroidXPx-0.5*labelw-5 );
      
      for( let otherindex = 0; !haveOverlap && otherindex < drawnlabels.length; ++otherindex ){
        let otherlabel = drawnlabels[otherindex];
        if( checkoverlap(label.node().getBBox(),otherlabel.node().getBBox()) ){
          haveOverlap = true;
          const x_overlap = xoverlap(label.node().getBBox(),otherlabel.node().getBBox());
          let newx = parseFloat(label.attr("x")) + x_overlap + 2;
          if( newx <= maxxpx ){
            haveOverlap = false;
            label.attr("x", newx );
            label.selectAll("tspan").each(function(d,i){ d3.select(this).attr("x", newx);});
            for( let testindex = 0; !haveOverlap && testindex < drawnlabels.length; ++testindex ){
              haveOverlap = checkoverlap(otherlabel.node().getBBox(),label.node().getBBox());
            }
          }//
        }//if( overlap )
      }//for( let otherindex = 0; !haveOverlap && otherindex < drawnlabels.length; ++otherindex )
      
      if( haveOverlap ){
        label.attr("x", labelx = origx );
        label.selectAll("tspan").each(function(d,i){ d3.select(this).attr("x", origx);});
        //console.log( 'Moving label right didnt help.' );
      } else {
        //console.log( 'Moving label right did help.' );
      }
    }//if( haveOverlap - try moving label to right )
    
    
    //If > 25% of chart height is avaiable under the chart - put the label down there if we can
    if( haveOverlap && (peak_ly < 0.75*charth) && ((peak_ly + labelh + 30) < charth) ){
      const starty = label.attr("y");
      let trial_y = peak_ly + 25;
      
      while( haveOverlap && ((trial_y + labelh + 5) < charth) ){
        haveOverlap = false;
        labely = trial_y;
        label.attr("y", trial_y );
        
        for( let otherindex = 0; !haveOverlap && otherindex < drawnlabels.length; ++otherindex ){
          let otherlabel = drawnlabels[otherindex];
          if( checkoverlap(label.node().getBBox(),otherlabel.node().getBBox()) ){
            haveOverlap = true;
            trial_y += 5 + yoverlap(label.node().getBBox(),otherlabel.node().getBBox());
            //ToDo: could try moving to the right (up to 50% label width), and
            //      if that is less than some percentage of the total change in y to avoid the overlap,
            //      than we could do that
          }
        }
      }//while( lowering label until no overlap )
      
      if( haveOverlap ){
        label.attr("y", starty );
      }
    }//if( haveOverlap - try putting label under spectrum )
    
    if( haveOverlap ){
      //I guess we're out of luck here, we couldnt find a place to put the label
      //  without it overlapping.
      //console.log( 'Failed to find a non-overlapping spot for ' + + ' label' );
    }
    
    drawnlabels.push( label );
  }//labelinfos.foreach(...)
  
}//SpectrumChartD3.prototype.drawPeakLabels = ...


/* Sets whether or not peaks are highlighted */
SpectrumChartD3.prototype.setShowPeaks = function(spectrum,show) {
  this.options.drawPeaksFor[spectrum] = show;
  this.redraw()();
}

SpectrumChartD3.prototype.setShowUserLabels = function(d) {
  this.options.showUserLabels = d;
  this.redraw()();
}

SpectrumChartD3.prototype.setShowPeakLabels = function(d) {
  //console.log('calling show peak labels = ', d);
  this.options.showPeakLabels = d;
  this.redraw()();
}

SpectrumChartD3.prototype.setShowNuclideNames = function(d) {
  this.options.showNuclideNames = d;
  this.redraw()();
}

SpectrumChartD3.prototype.setShowNuclideEnergies = function(d) {
  this.options.showNuclideEnergies = d;
  this.redraw()();
}


/**
 * -------------- Peak Fit Functions --------------
 */

SpectrumChartD3.prototype.erasePeakFitReferenceLines = function() {
  var self = this;

  /* Delete the leftmost start line */
  d3.select("#createPeakMouseStartLine").remove();
  
  /* Delete the right most current mouse line */
  d3.select("#createPeakMouseCurrentLine").remove(); 

  /* Delete the arrow definitions pointing to the mouse lines */
  d3.select("#createPeakStartArrowDef").remove();

  /* Delete the estimated continuum text */
  d3.select("#contEstText").remove();

  /* Delete the arrows pointing to the mouse lines */
  d3.selectAll(".createPeakArrow").forEach(function (arrows) {
    arrows.forEach(function(arrow) {
      arrow.remove();
    })
  });

  /* Delete the arrow lines for the previous arrows */
  d3.selectAll(".createPeakArrowLine").forEach(function (lines) {
    lines.forEach(function(line) {
      line.remove();
    })
  });

  /* Delete the all the lines for the estimated continuum */
  d3.selectAll(".createPeakContEstLine").forEach(function (lines) {
    lines.forEach(function(line) {
      line.remove();
    })
  });

  /* Delete the reference text for the create peak */
  d3.select("#createPeakMouseText").remove();
}


SpectrumChartD3.prototype.handleMouseMovePeakFit = function() {
/* ToDo:
     - implement if you hit the 1,2,3,4,... key while doing this, then it will force that many peaks to be fit for.
     - implement choosing different order polynomials while fitting, maybe l,c,q?
     - implement returning zero amplitude peak when fit fails in c++
     - cleanup naming of the temporary ROI and such to be consistent with handleRoiDrag and updateRoiBeingDragged
     - could maybe generalize the debounce mechanism
     - get this code working with touches (and in fact get touch code to just call this function)
     - remove/cleanup a number of functions like: erasePeakFitReferenceLines, handleTouchMovePeakFit, handleCancelTouchPeakFit
 */

  var self = this;
  
  //console.log( "In handleMouseMovePeakFit + " + d3.mouse(self.vis[0][0])[0] );

  /* If no spectra - bail */
  if( !self.rawData || !self.rawData.spectra || !self.rawData.spectra.length
      || self.rawData.spectra[0].y.length == 0 || this.rawData.spectra[0].y.length < 10 ) {
    return;
  }
  
  d3.select('body').style("cursor", "ew-resize");
  
  self.peakFitMouseMove = d3.mouse(self.vis[0][0]);
  self.peakFitTouchMove = d3.touches(self.vis[0][0]);
  
  let leftpospx, rightpospx;
  if( self.peakFitTouchMove.length > 0 ) {
    leftpospx = self.peakFitTouchMove[0][0] < self.peakFitTouchMove[1][0] ? self.peakFitTouchMove[0][0] : self.peakFitTouchMove[1][0];
    rightpospx = leftTouch === self.peakFitTouchMove[0] ? self.peakFitTouchMove[1][0] : self.peakFitTouchMove[0][0];
  } else {
    if( !self.leftMouseDown || !self.peakFitMouseMove ) {
      console.log( 'Hit condition I didnt think would happen fitting roi as dragging.' );
      return;
    }
    
    leftpospx = self.leftMouseDown[0];  //self.peakFitMouseDown[0]  //I think we can eliminate self.peakFitMouseDown now
    rightpospx = self.peakFitMouseMove[0];
    if( rightpospx < leftpospx )
      leftpospx = [rightpospx, rightpospx=leftpospx][0];
  }

  const lowerEnergy = self.xScale.invert(leftpospx);
  const upperEnergy = self.xScale.invert(rightpospx);
  
  self.zooming_plot = false;

  if( typeof self.zoominx0 !== 'number' )
    self.zoominx0 = self.xScale.invert(leftpospx);
  
  /* Set the original X-domain if it does not exist */
  if( !self.origdomain )
    self.origdomain = self.xScale.domain();
  
  /*This next line is a hack to get around how D3 is managing the zoom, but we highkacked it for the peak fitting  */
  self.xScale.domain( self.origdomain );
  
  let pageX = d3.event.pageX; //((d3.event && d3.event.pageX) ? d3.event.pageX : window.pageXOffset + leftpospx + ;
  let pageY = d3.event.pageY;
  //if( ){
  //  var bodyRect = document.body.getBoundingClientRect(),
  //  elemRect = element.getBoundingClientRect(),
  //  offset   = elemRect.top - bodyRect.top;
  //}
  
  //Emit current position, no more often than every 2.5 seconds, or if there
  //  are no requests pending.
  let emitFcn = function(){
    self.roiDragRequestTime = new Date();
    window.clearTimeout(self.roiDragRequestTimeout);
    self.roiDragRequestTimeout = null;
    self.roiDragRequestTimeoutFcn = null;
    
    //(window.pageXOffset + matrix.e + 15) + "px")
    //(window.pageYOffset + matrix.f - 30)
    
    console.log( 'd3.event.pageX=' + pageX + ', d3.event.pageY=' + pageY );
    self.WtEmit(self.chart.id, {name: 'fitRoiDrag'},
                lowerEnergy, upperEnergy, -1 /*self.forcedFitRoiNumPeaks*/, false, pageX, pageY );
  };
  
  let timenow = new Date();
  if( self.roiDragRequestTime === null || (timenow-self.roiDragRequestTime) > 2500 ){
    emitFcn();
  } else {
    let dt = Math.min( 2500, Math.max(0, 2500 - (timenow - self.roiDragRequestTime)) );
    window.clearTimeout( self.roiDragRequestTimeout );
    self.roiDragRequestTimeoutFcn = emitFcn;
    self.roiDragRequestTimeout = window.setTimeout( function(){
      if(self.roiDragRequestTimeoutFcn)
      self.roiDragRequestTimeoutFcn();
    }, dt );
  }
}//handleMouseMovePeakFit



SpectrumChartD3.prototype.handleTouchMovePeakFit = function() {
  var self = this;

  if (!self.rawData || !self.rawData.spectra)
    return;

  /* Clear the delete peaks mode */
  self.handleCancelTouchDeletePeak();

  /* Clear the count gammas mode */
  self.handleCancelTouchCountGammas();

  /* Cancel the zoom-in y mode */
  self.handleTouchCancelZoomInY();


  var t = d3.touches(self.vis[0][0]);

  /* Cancel the function if no two-finger swipes detected */
  if (!t || t.length !== 2 || !self.createPeaksStartTouches) {
    self.handleCancelTouchPeakFit();
    return;
  }

  /* Set the touch variables */
  var leftStartTouch = self.createPeaksStartTouches[0][0] < self.createPeaksStartTouches[1][0] ? self.createPeaksStartTouches[0] : self.createPeaksStartTouches[1],
      rightStartTouch = leftStartTouch === self.createPeaksStartTouches[0] ? self.createPeaksStartTouches[1] : self.createPeaksStartTouches[0];

  var leftTouch = t[0][0] < t[1][0] ? t[0] : t[1],
      rightTouch = leftTouch === t[0] ? t[1] : t[0];

  /* Cancel the action if the left touch is to the left touch is to the left of the original starting left touch */
  /* or if the left touch goes out of bounds */
  if (leftTouch[0] < leftStartTouch[0] || leftTouch[0] > self.xScale.invert(self.xScale.domain()[1])) {
    self.handleCancelTouchPeakFit();
    return;
  }

  rightTouch[0] = Math.min(rightTouch[0], self.xScale.range()[1]);

  //if( !self.fittingPeak )
  //  self.forcedFitRoiNumPeaks = -1;
  
  self.fittingPeak = true;
  

  self.setYAxisDomain();
  if (!self.yAxisZoomedOutFully) {
    self.redraw()();
  }

  /* Uncomment if you want to have peak fitting animation within touch */
  /* self.handleMouseMovePeakFit(); */

  /* Set the length of the arrows */
  var arrowLength = 25,
      arrowPadding = 7;

  /* Finger touch pixel size = 57 */
  var touchPointRadius = 20; 

  /* To keep track of some of the line objects being drawn */
  var createPeakTouchCurrentLine,
      contEstLine, 
      contEstText = d3.select("#contEstText"),
      createPeakTouchText1 = d3.select("#createPeakTouchText1"),
      createPeakTouchText2 = d3.select("#createPeakTouchText2"),
      createPeakRightTouchPointTop = d3.select("#createPeakRightTouchPointTop"),
      createPeakRightTouchPointBottom = d3.select("#createPeakRightTouchPointBottom"),
      createPeakTouchLineTop = d3.select("#createPeakTouchLineTop"), 
      createPeakTouchLineBottom = d3.select("#createPeakTouchLineBottom"),
      createPeakTouchArrowLineTop = d3.select("#createPeakTouchArrowLineTop"),
      createPeakTouchArrowLineBottom = d3.select("#createPeakTouchArrowLineBottom");

  if (createPeakTouchArrowLineTop.empty()) {
    createPeakTouchArrowLineTop = self.vis.append("line")
      .attr("id", "createPeakTouchArrowLineTop")
      .attr("class", "createPeakArrowLine")
      .attr("x1", leftStartTouch[0] - 12)
      .attr("x2", leftStartTouch[0] - 12)
      .attr("y1", leftStartTouch[1] - touchPointRadius - 20)
      .attr("y2", leftStartTouch[1] - touchPointRadius - 10);

    var createPeakTouchTopArrow = self.vis.append('svg:defs').attr("id", "createPeakStartArrowDef")
                          .append("svg:marker")
                          .attr("id", "createPeakTouchTopArrow")
                          .attr('class', 'createPeakArrow')
                          .attr("refX", 2)
                          .attr("refY", 8)
                          .attr("markerWidth", 25)
                          .attr("markerHeight", 25)
                          .attr("orient", 90)
                          .append("path")
                            .attr("d", "M2,2 L2,13 L8,7 L2,2")
                            .style("stroke", "black");

    createPeakTouchArrowLineTop.attr("marker-end", "url(#createPeakTouchTopArrow)");
  }
  if (createPeakTouchArrowLineBottom.empty()) {
    createPeakTouchArrowLineBottom = self.vis.append("line")
      .attr("id", "createPeakTouchArrowLineBottom")
      .attr("class", "createPeakArrowLine")
      .attr("x1", leftStartTouch[0] - 12)
      .attr("x2", leftStartTouch[0] - 12)
      .attr("y1", leftStartTouch[1] + touchPointRadius + 10)
      .attr("y2", leftStartTouch[1] + touchPointRadius + 20);

    var createPeakTouchBottomArrow = self.vis.append('svg:defs').attr("id", "createPeakStartArrowDef")
                          .append("svg:marker")
                          .attr("id", "createPeakTouchBottomArrow")
                          .attr('class', 'createPeakArrow')
                          .attr("refX", 2)
                          .attr("refY", 8)
                          .attr("markerWidth", 25)
                          .attr("markerHeight", 25)
                          .attr("orient", 270)
                          .append("path")
                            .attr("d", "M2,2 L2,13 L8,7 L2,2")
                            .style("stroke", "black");

    createPeakTouchArrowLineBottom.attr("marker-start", "url(#createPeakTouchBottomArrow)");
  }


  /* Create the left topmost and bottommost touch point */
  if (d3.select("#createPeakTouchPoint1").empty()) {
    self.vis.append("circle")
      .attr("id", "createPeakTouchPoint1")
      .attr("class", "createPeakLeftTouchPoint")
      .attr("cx", leftStartTouch[0])
      .attr("cy", leftStartTouch[1] - touchPointRadius)
      .attr("r", 3);
  }
  if (d3.select("#createPeakTouchPoint2").empty()) {
    self.vis.append("circle")
      .attr("id", "createPeakTouchPoint2")
      .attr("class", "createPeakLeftTouchPoint")
      .attr("cx", leftStartTouch[0])
      .attr("cy", leftStartTouch[1] + touchPointRadius)
      .attr("r", 3);
  }

  /* Create/update the right topmost and bottommost touch point */
  if (createPeakRightTouchPointTop.empty()) {
    createPeakRightTouchPointTop = self.vis.append("circle")
      .attr("id", "createPeakRightTouchPointTop")
      .attr("class", "createPeakRightTouchPoint")
      .attr("cy", leftStartTouch[1] - touchPointRadius)
      .attr("r", 3);
  }
  createPeakRightTouchPointTop.attr("cx", rightTouch[0]);

  if (createPeakRightTouchPointBottom.empty()) {
    createPeakRightTouchPointBottom = self.vis.append("circle")
      .attr("id", "createPeakRightTouchPointBottom")
      .attr("class", "createPeakRightTouchPoint")
      .attr("cy", leftStartTouch[1] + touchPointRadius)
      .attr("r", 3);
  }
  createPeakRightTouchPointBottom.attr("cx", rightTouch[0]);

  /* Create/update the touch lines */
  if (createPeakTouchLineTop.empty()) {
    createPeakTouchLineTop = self.vis.append("line")
      .attr("id", "createPeakTouchLineTop")
      .attr("class", "createPeakTouchLine")
      .attr("x1", leftStartTouch[0])
      .attr("y1", leftStartTouch[1] - touchPointRadius)
      .attr("y2", leftStartTouch[1] - touchPointRadius);
  }
  createPeakTouchLineTop.attr("x2", rightTouch[0]);

  if (createPeakTouchLineBottom.empty()) {
    createPeakTouchLineBottom = self.vis.append("line")
      .attr("id", "createPeakTouchLineBottom")
      .attr("class", "createPeakTouchLine")
      .attr("x1", leftStartTouch[0])
      .attr("y1", leftStartTouch[1] + touchPointRadius)
      .attr("y2", leftStartTouch[1] + touchPointRadius);
  }
  createPeakTouchLineBottom.attr("x2", rightTouch[0]);

  /* Create the leftmost starting point line  */
  if (d3.select("#createPeakTouchStartLine").empty()) {
    self.vis.append("line")
      .attr("id", "createPeakTouchStartLine")
      .attr("class", "createPeakMouseLine")
      .attr("x1", leftStartTouch[0])
      .attr("x2", leftStartTouch[0])
      .attr("y1", 0)
      .attr("y2", self.size.height);
  }

  /* Create/refer the rightmost current point line */
  if (d3.select("#createPeakTouchCurrentLine").empty()) {
    createPeakTouchCurrentLine = self.vis.append("line")
      .attr("id", "createPeakTouchCurrentLine")
      .attr("class", "createPeakMouseLine")
      .attr("y1", 0)
      .attr("y2", self.size.height);

  } else 
    createPeakTouchCurrentLine = d3.select("#createPeakTouchCurrentLine");

  createPeakTouchCurrentLine.attr("x1", rightTouch[0])
    .attr("x2", rightTouch[0]);

  /* Create the text for the touch level */
  if (createPeakTouchText1.empty())
    createPeakTouchText1 = self.vis.append("text")
      .attr("id", "createPeakTouchText1")
      .attr("class", "createPeakTouchText")
      .attr("y", leftStartTouch[1] - 2)
      .text("Keep fingers");
  createPeakTouchText1.attr("x", leftStartTouch[0] - createPeakTouchText1[0][0].clientWidth - 5);

  if (createPeakTouchText2.empty())
    createPeakTouchText2 = self.vis.append("text")
      .attr("id", "createPeakTouchText2")
      .attr("class", "createPeakTouchText")
      .attr("y", leftStartTouch[1] + 8)
      .text("level");
  createPeakTouchText2.attr("x", leftStartTouch[0] - createPeakTouchText2[0][0].clientWidth - 25);

  /* Create/refer to the text for the approx continuum */
  if (contEstText.empty()) {
    contEstText = self.vis.append("text")
      .attr("id", "contEstText")
      .attr("class", "contEstLineText")
      .text("approx continuum to use");
  }

  /* Get pixelated coordinates of mouse/starting positions of lines and coordinates */
  var coordsX0 = self.xScale.invert(leftStartTouch[0]),
      coordsY0 = self.getCountsForEnergy(self.rawData.spectra[0], coordsX0),
      coordsX1 = self.xScale.invert(rightTouch[0]),
      coordsY1 = self.getCountsForEnergy(self.rawData.spectra[0], coordsX1),
      x0 = leftStartTouch[0],
      x1 = rightTouch[0],
      y0 = self.yScale( coordsY0 ),
      y1 = self.yScale( coordsY1 ),
      dy = coordsY1 - coordsY0,
      lineAngle = (180/Math.PI) * Math.atan( (y1-y0)/(x1-x0) );

  /* Update the position and rotation of the continuum text using the pixelated coordinates */
  contEstText.attr("x", x0 + (Math.abs(x0-x1)/2) - Number(contEstText[0][0].clientWidth)/2 )
    .attr("y", y0-15)
    .attr("transform", "rotate(" + (!isNaN(lineAngle) ? lineAngle : 0) + ", " + (x0 + ((x1-x0)/2)) + ", " + y0 + ")");


  /* Create/refer to the reference text for creating a peak */
  if (d3.select("#createPeakTouchText").empty())
    createPeakTouchText = self.vis.append("text")
      .attr("id", "createPeakTouchText")
      .attr("class", "mouseLineText")
      .attr("y", self.size.height/5)
      .text("Will create peak Inside");
  else
    createPeakTouchText = d3.select("#createPeakTouchText");

  /* Move the create peaks text in the middle of the create peak mouse lines */
  createPeakTouchText.attr("x", x0 + (Math.abs(x0-x1)/2) - Number(createPeakTouchText[0][0].clientWidth)/2 );


  /* Remove the continuum estimation line (lines in this case, we create the effect using a numver of shorter 5px lines) */
  d3.selectAll(".createPeakContEstLine").forEach(function (lines) {
    lines.forEach(function(line) {
      line.remove();
    })
  });

  /* Get the end coordinates of the first (5px) line in the estimated continuum */
  var xpix = x0+5,
      ypix = self.yScale( coordsY0+dy*(xpix-x0)/(x1-x0) );

  /* Stop updating if the y-coordinate could not be found for the line */
  if (isNaN(ypix))
    return;

  /* Create the first 5px line for the estimated continuum */
  if (x1 > x0)
    contEstLine = self.vis.append("line")
      .attr("id", "contEstLine")
      .attr("class", "createPeakContEstLine")
      .attr("x1", x0)
      .attr("y1", y0)
      .attr("x2", xpix)
      .attr("y2", ypix);

  /* Create and update the next 5px lines until you reach the end for the estimated continuum */
  while (xpix < x1) {
    x0 = xpix;
    y0 = ypix;
    xpix += 5;
    ypix = self.yScale( coordsY0+dy*(xpix-leftStartTouch[0])/(x1-leftStartTouch[0]) );

    contEstLine = self.vis.append("line")
      .attr("id", "contEstLine")
      .attr("class", "createPeakContEstLine")
      .attr("x1", x0)
      .attr("y1", y0)
      .attr("x2", xpix)
      .attr("y2", ypix);
  }

  /* Create the last 5px line for the estimated continuum line */
  contEstLine = self.vis.append("line")
    .attr("id", "contEstLine")
    .attr("class", "createPeakContEstLine")
    .attr("x1", x0)
    .attr("y1", y0)
    .attr("x2", x1-2)
    .attr("y2", y1);
}

SpectrumChartD3.prototype.handleTouchEndPeakFit = function() {
  var self = this;

  var t = self.lastTouches;

  /* Cancel the function if no two-finger swipes detected */
  if (!t || t.length !== 2 || !self.createPeaksStartTouches) {
    self.handleCancelTouchPeakFit();
    return;
  }

  /* Set the touch variables */
  var leftStartTouch = self.createPeaksStartTouches[0][0] < self.createPeaksStartTouches[1][0] ? self.createPeaksStartTouches[0] : self.createPeaksStartTouches[1],
      rightStartTouch = leftStartTouch === self.createPeaksStartTouches[0] ? self.createPeaksStartTouches[1] : self.createPeaksStartTouches[0];

  var leftTouch = t[0][0] < t[1][0] ? t[0] : t[1],
      rightTouch = leftTouch === t[0] ? t[1] : t[0];

  /* Emit the create peak signal */
  if (self.controlDragSwipe && self.createPeaksStartTouches && self.lastTouches) {
    console.log("Emit CREATE PEAK signal from x0 = ", leftStartTouch[0], "(", self.xScale.invert(leftStartTouch[0]), 
      " kEV) to x1 = ", rightTouch[0], "(", self.xScale.invert(rightTouch[0]), 
      " kEV)");
    self.WtEmit(self.chart.id, {name: 'controlkeydragged'}, self.xScale.invert(leftStartTouch[0]), self.xScale.invert(rightTouch[0]), d3.event.pageX, d3.event.pageY);
  }

  /* Delete all the create peak elements */
  self.handleCancelTouchPeakFit();
}

SpectrumChartD3.prototype.handleCancelTouchPeakFit = function() {
  var self = this;

  /* Delete the leftmost start line */
  d3.select("#createPeakTouchStartLine").remove();
  
  /* Delete the right most current mouse line */
  d3.select("#createPeakTouchCurrentLine").remove(); 

  /* Delete the arrow definitions pointing to the mouse lines */
  d3.select("#createPeakStartArrowDef").remove();

  /* Delete the estimated continuum text */
  d3.select("#contEstText").remove();

  /* Delete the arrows pointing to the mouse lines */
  d3.selectAll(".createPeakArrow").forEach(function (arrows) {
    arrows.forEach(function(arrow) {
      arrow.remove();
    })
  });

  /* Delete the arrow lines for the previous arrows */
  d3.selectAll(".createPeakArrowLine").forEach(function (lines) {
    lines.forEach(function(line) {
      line.remove();
    })
  });

  /* Delete the touch points */
  d3.selectAll(".createPeakLeftTouchPoint").forEach(function (points) {
    points.forEach(function(point) {
      point.remove();
    })
  });
  d3.selectAll(".createPeakRightTouchPoint").forEach(function (points) {
    points.forEach(function(point) {
      point.remove();
    })
  });

  /* Delete the touch lines */
  d3.selectAll(".createPeakTouchLine").forEach(function (lines) {
    lines.forEach(function(line) {
      line.remove();
    })
  });

  /* Delete the all the lines for the estimated continuum */
  d3.selectAll(".createPeakContEstLine").forEach(function (lines) {
    lines.forEach(function(line) {
      line.remove();
    })
  });

  /* Delete the reference text for the create peak */
  d3.select("#createPeakTouchText").remove();
  d3.selectAll(".createPeakTouchText").forEach(function (texts) {
    texts.forEach(function(text) {
      text.remove();
    })
  });

  self.controlDragSwipe = false;
  self.fittingPeak = null;
}

/*Function called when use lets the mouse button up */
SpectrumChartD3.prototype.handleMouseUpPeakFit = function() {
  var self = this;

  const roi = self.roiBeingDrugUpdate;
  if( !self.fittingPeak || !self.rawData || !self.rawData.spectra || !roi )
    return;

  console.log( 'Mouse up during peak fit' );

  self.fittingPeak = null;
  
  self.redraw()();
  self.handleCancelRoiDrag();
  
  if( self.leftMouseDown ) {
    const pageX = d3.event.pageX;
    const pageY = d3.event.pageY;
    //const x0 = self.leftMouseDown[0],
    //      x1 = d3.mouse(self.vis.node())[0];
    //self.WtEmit(self.chart.id, {name: 'fitRoiDrag'}, x0, x1, -1, true );
    //Instead of updating with any movements the mouse may have made, leaving the final fit result
    //  different than whats currently showing; should re-evaluate after using for a while
    console.log( 'd3.event.pageX=' + pageX + ", d3.event.pageY=" + pageY );
    self.WtEmit( self.chart.id, {name: 'fitRoiDrag'},
                 roi.lowerEnergy, roi.upperEnergy, roi.peaks.length, true, pageX, pageY );
  }
}

/*Function called when you hit escape while fitting peak */
SpectrumChartD3.prototype.handleCancelMousePeakFit = function() {
  console.log( 'Canceled peakfit' );
  this.handleCancelRoiDrag();
}


/**
 * -------------- Peak Marker Functions --------------
 */
SpectrumChartD3.prototype.updateFeatureMarkers = function(sumPeaksArgument) {
  var self = this;

  /* Christian: Just catching this weird error whenever user initially clicks the checkbox for one of the feature markers.
                I'm guessing it is thrown because the mouse does not exist for the vis element, so we don't update the feature markers.
   */
  try {
    d3.mouse(self.vis[0][0])
  } catch (error) {
    console.log( "Error thrown: source event is null" );
    return;
  }

  /* Positional variables (for mouse and touch) */
  var m = d3.mouse(self.vis[0][0]),
      t = d3.touches(self.vis[0][0]);

  /* Adjust the mouse position accordingly to touch (because some of these functions use mouse position in touch devices) */
  if (t.length > 0)
    m = t[0];

  /* Chart coordinate values */
  var energy = self.xScale.invert(m[0]),
      xmax = self.size.width,
      ymax = self.size.height;

  /* Do not update feature markers if legend being dragged or energy value is undefined */
  if ((t && self.legdown) || isNaN(energy))
    return;
  if (self.currentlyAdjustingSpectrumScale)
    return;

  var cursorIsOutOfBounds = (t && t.length > 0) ? (t[0][0] < 0 || t[0][0] > xmax) : (m[0] < 0  || m[0] > xmax || m[1] < 0 || m[1] > ymax);

  
  let axiscolor = 'black', txtcolor = 'black';
  const tickElement = document.querySelector('.tick');
  const tickStyle = tickElement ? getComputedStyle(tickElement) : null;
  axiscolor = tickStyle && tickStyle.stroke ? tickStyle.stroke : 'black';
  
  const titleElement = document.querySelector('.xaxistitle');
  const titleStyle = titleElement ? getComputedStyle(titleElement) : null;
  txtcolor = titleStyle && titleStyle.stroke ? titleStyle.stroke : 'black';
  
  //Spacing between lines of text
  let linehspace = 13;

  /* Mouse-edge Helpers: These are global helpers for feature markers that update the mouse edge position.
  */

  /* Mouse edge should be deleted if: 
      none of the scatter/escape peak options are unchecked 
      OR if cursor is out of bounds 
      OR if the user is currently dragging in the graph
  */
  function shouldDeleteMouseEdge() {
    return (!self.options.showComptonEdge && !self.options.showComptonPeaks && !self.options.showEscapePeaks && !self.options.showSumPeaks) || 
    cursorIsOutOfBounds || 
    self.dragging_plot;
  }
  function deleteMouseEdge( shouldDelete ) {
    if ( shouldDelete || shouldDeleteMouseEdge() )
    {
      if ( self.mouseEdge ) {
        self.mouseEdge.remove(); 
        self.mouseEdge = null;
      }
      if ( self.mouseEdgeText ) {
        self.mouseEdgeText.remove(); 
        self.mouseEdgeText = null;
      }
      return true;
    }
    return false;
  }
  function updateMouseEdge() {

    /* If mouse edge could has been deleted, do not update the mouse edge */
    if (deleteMouseEdge())
      return;

    /* Update the mouse edge and corresponding text position  */
    if ( self.mouseEdge ) {
        self.mouseEdge
          .attr("stroke", axiscolor)
          .attr("x1", m[0])
          .attr("x2", m[0])
          .attr("y2", self.size.height);
        self.mouseEdgeText
          .attr( "fill", txtcolor )
          .attr( "y", self.size.height/4)
          .attr( "x", m[0] + xmax/125 )
          .text( energy.toFixed(1) + " keV");
    } else {  
        /* Create the mouse edge (and text next to it) */
        self.mouseEdge = self.vis.append("line")
          .attr("class", "mouseLine")
          .attr("stroke-width", 2)
          .attr("stroke", axiscolor)
          .attr("x1", m[0])
          .attr("x2", m[0])
          .attr("y1", 0)
          .attr("y2", self.size.height);

        self.mouseEdgeText = self.vis.append("text")
          .attr("class", "mouseLineText")
          .attr( "fill", txtcolor )
          .attr( "x", m[0] + xmax/125 )
          .attr( "y", self.size.height/4)
          .text( energy.toFixed(1) + " keV");
    }
    
    self.mouseEdge.attr("stroke", axiscolor);
  }


  function updateEscapePeaks() {
    /* Calculations for the escape peak markers */
    var singleEscapeEnergy = energy - 510.99891,
        singleEscapePix = self.xScale(singleEscapeEnergy),

        singleEscapeForwardEnergy = energy + 510.99891,
        singleEscapeForwardPix = self.xScale(singleEscapeForwardEnergy),

        doubleEscapeEnergy = energy - 1021.99782,
        doubleEscapePix = self.xScale(doubleEscapeEnergy),

        doubleEscapeForwardEnergy = energy + 1021.99782,
        doubleEscapeForwardPix = self.xScale(doubleEscapeForwardEnergy);

    /* Deletes the marker for a single escape peak */
    function deleteSingleEscape() {
      if( self.singleEscape ) {
        self.singleEscape.remove();
        self.singleEscape = null;
      }
      if ( self.singleEscapeText ) {
          self.singleEscapeText.remove();
          self.singleEscapeText = null;
      }
      if ( self.singleEscapeMeas ) {
          self.singleEscapeMeas.remove();
          self.singleEscapeMeas = null;
      }
    }

    /* Deletes the marker for a double escape peak */
    function deleteDoubleEscape() {
      if ( self.doubleEscape ) {
        self.doubleEscape.remove();
        self.doubleEscape = null;
      }
      if ( self.doubleEscapeText ) {
        self.doubleEscapeText.remove();
        self.doubleEscapeText = null;
      }
      if ( self.doubleEscapeMeas ) {
        self.doubleEscapeMeas.remove();
        self.doubleEscapeMeas = null;
      }
    }
    /* Deletes the marker for a single forward escape peak */
    function deleteSingleEscapeForward() {
      if ( self.singleEscapeForward ) {
        self.singleEscapeForward.remove();
        self.singleEscapeForward = null;
      }
      if ( self.singleEscapeForwardText ) {
          self.singleEscapeForwardText.remove();
          self.singleEscapeForwardText = null;
      }
      if ( self.singleEscapeForwardMeas ) {
          self.singleEscapeForwardMeas.remove();
          self.singleEscapeForwardMeas = null;
      }
    }

    /* Deletes the marker for a double forward escape peak */
    function deleteDoubleEscapeForward() {
      if ( self.doubleEscapeForward ) {
        self.doubleEscapeForward.remove();
        self.doubleEscapeForward = null;
      }
      if ( self.doubleEscapeForwardText ) {
          self.doubleEscapeForwardText.remove();
          self.doubleEscapeForwardText = null;
      }
      if ( self.doubleEscapeForwardMeas ) {
          self.doubleEscapeForwardMeas.remove();
          self.doubleEscapeForwardMeas = null;
      }
    }

    if (shouldDeleteMouseEdge())
      deleteMouseEdge(true);
    
    if( !self.options.showEscapePeaks || cursorIsOutOfBounds || self.dragging_plot ) {
      deleteSingleEscape();
      deleteDoubleEscape();
      deleteSingleEscapeForward();
      deleteDoubleEscapeForward();
      return;
    }

    var singleEscapeOutOfBounds = singleEscapePix < 0 || singleEscapePix > xmax,
        doubleEscapeOutOfBounds = doubleEscapePix < 0 || doubleEscapePix > xmax,
        singleEscapeForwardOutOfBounds = singleEscapeForwardPix < 0 || singleEscapeForwardPix > xmax,
        doubleEscapeForwardOutOfBounds = doubleEscapeForwardPix < 0 || doubleEscapeForwardPix > xmax;

    if ( doubleEscapeOutOfBounds ) {
      deleteDoubleEscape();

      if ( singleEscapeOutOfBounds )
        deleteSingleEscape();
    }

    if ( doubleEscapeForwardOutOfBounds ) {
      deleteDoubleEscapeForward();

      if ( singleEscapeForwardOutOfBounds )
        deleteSingleEscapeForward();
    }

    updateMouseEdge();

    if (!singleEscapeForwardOutOfBounds) {
      if( !self.singleEscapeForward && singleEscapeForwardEnergy >= 0 ) {  
        self.singleEscapeForward = self.vis.append("line")    /* create single forward escape line */
        .attr("class", "escapeLineForward")
        .attr("stroke", axiscolor)
        .attr("x1", singleEscapeForwardPix)
        .attr("x2", singleEscapeForwardPix)
        .attr("y1", 0)
        .attr("y2", self.size.height);
      self.singleEscapeForwardText = self.vis.append("text") /* create Single Forward Escape label beside line */
            .attr("class", "peakText")
            .attr( "fill", txtcolor )
            .attr( "x", singleEscapeForwardPix + xmax/200 )
            .attr( "y", self.size.height/5.3)
            .text( "Single Escape" );
      self.singleEscapeForwardMeas = self.vis.append("text") /* Create measurement label besides line, under Single Escape label */
            .attr("class", "peakText")
            .attr( "fill", txtcolor )
            .attr( "x", singleEscapeForwardPix + xmax/125 )
            .attr( "y", self.size.height/5.3 + linehspace)
            .text( singleEscapeForwardEnergy.toFixed(1) + " keV" );
      } else {
        if ( singleEscapeForwardEnergy < 0 && self.singleEscapeForward && self.singleEscapeForwardText && self.singleEscapeForwardMeas ) {
          deleteSingleEscapeForward();

        } else if ( self.singleEscapeForward ) {      /* Move everything to where mouse is */
          self.singleEscapeForward
            .attr("stroke", axiscolor)
            .attr("y2", self.size.height)
            .attr("x1", singleEscapeForwardPix)
            .attr("x2", singleEscapeForwardPix);
          self.singleEscapeForwardText
            .attr( "fill", txtcolor )
            .attr( "y", self.size.height/5.3)
            .attr( "x", singleEscapeForwardPix + xmax/200 );
          self.singleEscapeForwardMeas
            .attr( "fill", txtcolor )
            .attr( "y", self.size.height/5.3 + linehspace)
            .attr( "x", singleEscapeForwardPix + xmax/125 )
            .text( singleEscapeForwardEnergy.toFixed(1) + " keV" );
        }
      }
    }

    if (!doubleEscapeForwardOutOfBounds) {
      if( !self.doubleEscapeForward && doubleEscapeForwardEnergy >= 0 ) {  
        self.doubleEscapeForward = self.vis.append("line")    /* create double forward escape line */
        .attr("class", "escapeLineForward")
        .attr("stroke", axiscolor)
        .attr("x1", doubleEscapeForwardPix)
        .attr("x2", doubleEscapeForwardPix)
        .attr("y1", 0)
        .attr("y2", self.size.height);
      self.doubleEscapeForwardText = self.vis.append("text") /* create double Forward Escape label beside line */
            .attr("class", "peakText")
            .attr( "fill", txtcolor )
            .attr( "x", doubleEscapeForwardPix + xmax/200 )
            .attr( "y", self.size.height/5.3)
            .text( "Double Escape" );
      self.doubleEscapeForwardMeas = self.vis.append("text") /* Create measurement label besides line, under double Escape label */
            .attr("class", "peakText")
            .attr( "fill", txtcolor )
            .attr( "x", doubleEscapeForwardPix + xmax/125 )
            .attr( "y", self.size.height/5.3 + linehspace)
            .text( doubleEscapeForwardEnergy.toFixed(1) + " keV" );
      } else {
        if ( doubleEscapeForwardEnergy < 0 && self.doubleEscapeForward && self.doubleEscapeForwardText && self.doubleEscapeForwardMeas ) {
          deleteDoubleEscapeForward();

        } else if ( self.doubleEscapeForward ) {      /* Move everything to where mouse is */
          self.doubleEscapeForward
            .attr("stroke", axiscolor)
            .attr("y2", self.size.height)
            .attr("x1", doubleEscapeForwardPix)
            .attr("x2", doubleEscapeForwardPix);
          self.doubleEscapeForwardText
            .attr( "fill", txtcolor )
            .attr( "y", self.size.height/5.3)
            .attr("x", doubleEscapeForwardPix + xmax/200 );
          self.doubleEscapeForwardMeas
            .attr( "fill", txtcolor )
            .attr( "x", doubleEscapeForwardPix + xmax/125 )
            .attr( "y", self.size.height/5.3 + linehspace)
            .text( doubleEscapeForwardEnergy.toFixed(1) + " keV" );
        }
      }
    }

    if ( singleEscapeOutOfBounds ) 
      return;

    /* Draw single escape peak if not present in the grapy */
    if( !self.singleEscape && singleEscapeEnergy >= 0 ) {  
      self.singleEscape = self.vis.append("line")    /* create single escape line */
      .attr("class", "peakLine")
      .attr("stroke", axiscolor)
      .attr("x1", singleEscapePix)
      .attr("x2", singleEscapePix)
      .attr("y1", 0)
      .attr("y2", self.size.height);
    self.singleEscapeText = self.vis.append("text") /* create Single Escape label beside line */
          .attr("class", "peakText")
          .attr( "fill", txtcolor )
          .attr( "x", singleEscapePix + xmax/200 )
          .attr( "y", self.size.height/5.3)
          .text( "Single Escape" );
    self.singleEscapeMeas = self.vis.append("text") /* Create measurement label besides line, under Single Escape label */
          .attr("class", "peakText")
          .attr( "fill", txtcolor )
          .attr( "x", singleEscapePix + xmax/125 )
          .attr( "y", self.size.height/5.3 + linehspace)
          .text( singleEscapeEnergy.toFixed(1) + " keV" );
    } else {
      if ( singleEscapeEnergy < 0 && self.singleEscape && self.singleEscapeText && self.singleEscapeMeas ) {
        self.singleEscape.remove();      /* Delete lines and labels if out of bounds */
        self.singleEscape = null;
        self.singleEscapeText.remove();
        self.singleEscapeText = null;
        self.singleEscapeMeas.remove();
        self.singleEscapeMeas = null;

      } else if ( self.singleEscape ) {      /* Move everything to where mouse is */
        self.singleEscape
          .attr("stroke", axiscolor)
          .attr("y2", self.size.height)
          .attr("x1", singleEscapePix)
          .attr("x2", singleEscapePix);
        self.singleEscapeText
          .attr( "fill", txtcolor )
          .attr( "y", self.size.height/5.3)
          .attr( "x", singleEscapePix + xmax/200 );
        self.singleEscapeMeas
          .attr( "fill", txtcolor )
          .attr( "x", singleEscapePix + xmax/125 )
          .attr( "y", self.size.height/5.3 + linehspace)
          .text( singleEscapeEnergy.toFixed(1) + " keV" );
      }
    }

    /* Do not update the double escape peak marker anymore */
    if (doubleEscapeOutOfBounds) 
      return;

      /* Draw double escape peak if not present in the grapy */
    if( !self.doubleEscape && doubleEscapeEnergy >= 0 ) {
      self.doubleEscape = self.vis.append("line")  /* create double escape line */
      .attr("class", "peakLine")
      .attr("stroke-width", 2)
      .attr("stroke", axiscolor)
      .attr("x1", doubleEscapePix)
      .attr("x2", doubleEscapePix)
      .attr("y1", 0)
      .attr("y2", self.size.height);
    self.doubleEscapeText = self.vis.append("text") /* create Double Escape label beside line */
          .attr("class", "peakText")
          .attr( "fill", txtcolor )
          .attr( "x", doubleEscapePix + xmax/200 )
          .attr( "y", self.size.height/5.3)
          .text( "Double Escape" );
    self.doubleEscapeMeas = self.vis.append("text") /* Create measurement label besides line, under Double Escape label */
          .attr("class", "peakText")
          .attr( "fill", txtcolor )
          .attr( "x", doubleEscapePix + xmax/125 )
          .attr( "y", self.size.height/5.3 + linehspace)
          .text( doubleEscapeEnergy.toFixed(1) + " keV" );
    } else {
      if ( (doubleEscapeEnergy < 0) && self.doubleEscape && self.doubleEscapeText && self.doubleEscapeMeas ) {
        self.doubleEscape.remove();    /* Delete lines and labels if out of bounds */
      self.doubleEscape = null;
          self.doubleEscapeText.remove();
          self.doubleEscapeText = null;
          self.doubleEscapeMeas.remove();
          self.doubleEscapeMeas = null;

      } else if ( self.doubleEscape ) {    /* Move everything to where mouse is */

        self.doubleEscape
          .attr("stroke", axiscolor)
          .attr("y2", self.size.height)
          .attr("x1", doubleEscapePix)
          .attr("x2", doubleEscapePix);
        self.doubleEscapeText
          .attr( "fill", txtcolor )
          .attr("x", doubleEscapePix + xmax/200 );
        self.doubleEscapeMeas
          .attr( "fill", txtcolor )
          .attr( "x", doubleEscapePix + xmax/125 )
          .text( doubleEscapeEnergy.toFixed(1) + " keV" );
      }
    }
  }

  function updateComptonPeaks() {

    var compAngleRad = self.options.comptonPeakAngle * (3.14159265/180.0)   /* calculate radians of compton peak angle */
    var comptonPeakEnergy = energy / (1 + ((energy/510.99891)*(1-Math.cos(compAngleRad)))); /* get energy value from angle and current energy position */
    var comptonPeakPix = self.xScale(comptonPeakEnergy);

    if (shouldDeleteMouseEdge())
      deleteMouseEdge(true);
    
    var comptonPeakOutOfBounds = comptonPeakPix < 0 || comptonPeakPix > xmax;

    /* delete if compton peak option is turned off or cursor is out of the graph */
    if( !self.options.showComptonPeaks || cursorIsOutOfBounds || comptonPeakOutOfBounds || self.dragging_plot ) {
      if( self.comptonPeak ) {
        self.comptonPeak.remove(); self.comptonPeak = null;
        /* console.log( 'Should emit compton peak closed' ); */
      }
      if ( self.comptonPeakText ) {
        self.comptonPeakText.remove(); self.comptonPeakText = null;
      }
      if ( self.comptonPeakMeas ) {
        self.comptonPeakMeas.remove(); self.comptonPeakMeas = null;
      }

      if (t.length == 0) {        /* if mouse movement (aka not touch movement), then update the mouse edge */
        updateMouseEdge();
      }

      return;
    }

    if( !self.comptonPeak ) {
      /* draw compton edge line here */
      self.comptonPeak = self.vis.append("line")
        .attr("class", "peakLine")
        .attr("stroke-width", 2)
        .attr("y1", 0);
      self.comptonPeakText = self.vis.append("text")
        .attr("class", "peakText")
        .attr( "y", self.size.height/10);
      self.comptonPeakMeas = self.vis.append("text")
        .attr("class", "peakText")
        .attr( "y", self.size.height/10 + linehspace);
    }
    
    self.comptonPeak
        .attr("stroke", axiscolor)
        .attr("y2", self.size.height)
        .attr("x1", comptonPeakPix)
        .attr("x2", comptonPeakPix);
      
    self.comptonPeakText
        .attr( "fill", txtcolor )
        .attr( "x", comptonPeakPix + xmax/200 )
        .text( self.options.comptonPeakAngle + "° Compton Peak" )
        
    self.comptonPeakMeas
        .attr( "fill", txtcolor )
        .attr( "x", comptonPeakPix + xmax/125 )
        .text( comptonPeakEnergy.toFixed(1) + " keV" );
    
    updateMouseEdge();
  }

  function updateComptonEdge() {

    var compedge = energy - (energy / (1 + (2*(energy/510.99891))));
    var compEdgePix = self.xScale(compedge);
    
    if ( shouldDeleteMouseEdge() ) 
      deleteMouseEdge(true);

    var comptonEdgeOutOfBounds = compEdgePix < 0  || compEdgePix > xmax ;

    /* delete if compton edge already if option is turned off or cursor is out of the graph */
    if( !self.options.showComptonEdge || cursorIsOutOfBounds || comptonEdgeOutOfBounds || self.dragging_plot ) {
      if( self.comptonEdge ) {
        self.comptonEdge.remove(); 
        self.comptonEdge = null;
      }
      if ( self.comptonEdgeText ) {
        self.comptonEdgeText.remove(); 
        self.comptonEdgeText = null;
      }
      if ( self.comptonEdgeMeas ) {
          self.comptonEdgeMeas.remove(); 
          self.comptonEdgeMeas = null;
      }

      updateMouseEdge();
      return;
    }
    
    if( !self.comptonEdge ) {
      /* draw compton edge line here */
      self.comptonEdge = self.vis.append("line")
        .attr("class", "peakLine")
        .attr("stroke-width", 2);
      self.comptonEdgeText = self.vis.append("text")
        .attr("class", "peakText")
        .text( "Compton Edge" );
      self.comptonEdgeMeas = self.vis.append("text")
        .attr("class", "peakText");
    }
    
    self.comptonEdge
        .attr("stroke", axiscolor)
        .attr("x1", compEdgePix)
        .attr("x2", compEdgePix)
        .attr("y1", 0)
        .attr("y2", self.size.height);
    self.comptonEdgeText
        .attr( "fill", txtcolor )
        .attr("x", compEdgePix + xmax/200 )
        .attr("y", self.size.height/22);
    self.comptonEdgeMeas
        .attr( "fill", txtcolor )
        .attr( "x", compEdgePix + xmax/125 )
        .attr( "y", self.size.height/22 + linehspace)
        .text( compedge.toFixed(1) + " keV" );
    
    updateMouseEdge();
  }

  function updateSumPeaks( clickedEnergy ) {

    function deleteClickedPeakMarker() {
      if( self.clickedPeak ) {
        self.clickedPeak.remove(); 
        self.clickedPeak = null;
      }
      if ( self.clickedPeakMeas ) {
        self.clickedPeakMeas.remove(); 
        self.clickedPeakMeas = null;
      }
    }

    function deleteSumPeakMarker() {
      if ( self.sumPeak ) {
        self.sumPeak.remove(); 
        self.sumPeak = null;
      }
      if ( self.sumPeakMeas ) {
        self.sumPeakMeas.remove(); 
        self.sumPeakMeas = null;
      }
      if ( self.sumPeakText ) {
          self.sumPeakText.remove(); 
          self.sumPeakText = null;
      }
    }

    function deleteLeftSumPeakMarker() {
      if ( self.leftSumPeak ) {
        self.leftSumPeak.remove(); 
        self.leftSumPeak = null;
      }
      if ( self.leftSumPeakMeas ) {
        self.leftSumPeakMeas.remove(); 
        self.leftSumPeakMeas = null;
      }
      if ( self.leftSumPeakText ) {
        self.leftSumPeakText.remove(); 
        self.leftSumPeakText = null;
      }
    }
    
    if ( shouldDeleteMouseEdge() ) 
      deleteMouseEdge(true);

    /* delete if sum peak option is already turned off or cursor is out of the graph */
    if( !self.options.showSumPeaks || cursorIsOutOfBounds || self.dragging_plot ) {
      /* delete the sum peak corresponding help text  */
      if ( self.sumPeakHelpText ) {
        self.sumPeakHelpText.remove(); 
        self.sumPeakHelpText = null;
      }

      if ( cursorIsOutOfBounds || self.dragging_plot ) {
        if ( self.clickedPeak ) {
          self.savedClickEnergy = self.xScale.invert( self.clickedPeak.attr("x1") );
        }
      } else if ( !self.options.showSumPeaks )
        self.savedClickEnergy = null;

      deleteClickedPeakMarker();
    }
    

    if( !self.options.showSumPeaks || cursorIsOutOfBounds || self.dragging_plot ) {
      deleteSumPeakMarker();
      deleteLeftSumPeakMarker();
      return;
    }

    if ( !self.options.showSumPeaks ) 
      self.savedClickEnergy = null;

    updateMouseEdge();

    var shouldUpdateClickedPeak = true,
        shouldUpdateSumPeak = true,
        shouldUpdateLeftSumPeak = true;

    if ( self.savedClickEnergy == null && clickedEnergy == null ) {
      shouldUpdateSumPeaks = shouldUpdateLeftSumPeak = shouldUpdateClickedPeak = false;
    }
    else if ( self.savedClickEnergy != null && (clickedEnergy == null || clickedEnergy < 0) )
      clickedEnergy = self.savedClickEnergy;
    else if ( clickedEnergy < 0 ) {
      if ( self.clickedPeak ) {
        self.savedClickEnergy = clickedEnergy = Number(self.clickedPeak.attr("energy")) ;
      }
      else shouldUpdateClickedPeak = false;
    }

    if ( !shouldUpdateClickedPeak && !shouldUpdateSumPeak && !shouldUpdateLeftSumPeak )
      return;

    var clickedEdgeOutOfBounds = false;
    if ( shouldUpdateClickedPeak ) {
      self.savedClickEnergy = null;

      var clickedEdgePix = self.xScale( clickedEnergy  );
      clickedEdgeOutOfBounds = clickedEdgePix < 0 || clickedEdgePix > xmax;

      if (clickedEdgeOutOfBounds) {
        self.savedClickEnergy = clickedEnergy;
        deleteClickedPeakMarker();
      } else {
        if( !self.clickedPeak ){
          /* draw compton edge line here */
          self.clickedPeak = self.vis.append("line")
              .attr("class", "peakLine")
              .attr("stroke-width", 2);
          self.clickedPeakMeas = self.vis.append("text")
              .attr("class", "peakText");
        }
        

        self.clickedPeak
            .attr("stroke", axiscolor)
            .attr("x1", clickedEdgePix)
            .attr("x2", clickedEdgePix)
            .attr("y1", 0)
            .attr("y2", self.size.height)
            .attr("energy", clickedEnergy);
        self.clickedPeakMeas
            .attr( "fill", txtcolor )
            .attr( "x", clickedEdgePix + xmax/125 )
            .attr( "y", self.size.height/4)
            .text( clickedEnergy.toFixed(1) + " keV" );
      }
    }  

    if ( !self.clickedPeak && !self.savedClickEnergy ) { 
      shouldUpdateSumPeak = false;

      if ( !self.sumPeakHelpText ) {
        /* create the sum peak help text */
        self.sumPeakHelpText = self.vis.append("text")
            .attr("class", "peakText")
            .attr("fill", "red")
            .text( "Click to set sum peak first energy." );
      }
      
      self.sumPeakHelpText
          .attr( "x", m[0] + xmax/125 )
          .attr( "y", self.size.height/3.5)
    } else {
        /* delete sum peak help text */
        if ( self.sumPeakHelpText ) {
          self.sumPeakHelpText.remove(); 
          self.sumPeakHelpText = null;
        }
    }

    if ( shouldUpdateLeftSumPeak && energy < clickedEnergy ) {
      var leftSumEnergy = clickedEnergy - energy,
          leftSumPix = self.xScale( leftSumEnergy  ),
          leftSumOutOfBounds = leftSumPix < 0 || leftSumPix > xmax;

      if( !self.leftSumPeak ) {
        /* draw left-sum peak line here */
        self.leftSumPeak = self.vis.append("line")
          .attr("class", "peakLine")
          .attr("stroke-width", 2);
        self.leftSumPeakText = self.vis.append("text")
          .attr("class", "peakText")
          .text( "Clicked Peak" );
        self.leftSumPeakMeas = self.vis.append("text")
          .attr("class", "peakText");
      }
      
      /* update the left sum peak line here */
      self.leftSumPeak
          .attr("stroke", axiscolor)
          .attr("x1", leftSumPix)
          .attr("x2", leftSumPix)
          .attr("y1", 0)
          .attr("y2", self.size.height); 
      self.leftSumPeakText
          .attr( "fill", txtcolor )
          .attr( "x", leftSumPix + xmax/125 )
          .attr( "y", self.size.height/3.4);
      self.leftSumPeakMeas
          .attr( "fill", txtcolor )
          .attr( "x", leftSumPix + xmax/125 )
          .attr( "y", self.size.height/3.4 + linehspace)
          .text( energy.toFixed(1) + "+" + leftSumEnergy.toFixed(1) + "=" + clickedEnergy.toFixed(1) + " keV" );

      if( leftSumOutOfBounds )
        deleteLeftSumPeakMarker();

    } else
      deleteLeftSumPeakMarker();


    if ( shouldUpdateSumPeak ) {
      var sumEnergy = energy + clickedEnergy,
          sumPix = self.xScale( sumEnergy  );

      var sumPeakOutOfBounds = sumPix < 0 || sumPix > xmax;
      if ( sumPeakOutOfBounds ) {
        deleteSumPeakMarker();
        return;
      }

      if (!clickedEnergy)
        return;

      if( !self.sumPeak ) {
        /* draw sum peak line here */
        self.sumPeak = self.vis.append("line")
          .attr("class", "peakLine")
          .attr("stroke-width", 2);
      self.sumPeakText = self.vis.append("text")
          .attr("class", "peakText")
          .text( "Sum Peak" );
      }
      
      if( !self.sumPeakMeas )
        self.sumPeakMeas = self.vis.append("text")
                .attr("class", "peakText");

      self.sumPeak
          .attr("stroke", axiscolor)
          .attr("x1", sumPix)
          .attr("x2", sumPix)
          .attr("y1", 0)
          .attr("y2", self.size.height);
      self.sumPeakText
          .attr( "fill", txtcolor )
          .attr( "x", sumPix + xmax/125 )
          .attr( "y", self.size.height/4);
      self.sumPeakMeas
          .attr( "fill", txtcolor )
          .attr( "x", sumPix + xmax/125 )
          .attr( "y", self.size.height/4 +  + linehspace)
          .text( clickedEnergy.toFixed(1) + "+" + energy.toFixed(1) + "=" + sumEnergy.toFixed(1) + " keV" );
    }
  }

  updateEscapePeaks();
  updateComptonPeaks();
  updateComptonEdge();
  updateSumPeaks(sumPeaksArgument);
}

SpectrumChartD3.prototype.setComptonEdge = function(d) {
  this.options.showComptonEdge = d;
  if ( d ) {
    this.updateFeatureMarkers();
  }
}

SpectrumChartD3.prototype.setComptonPeakAngle = function(d) {
  var value = Number(d);
  if (!isNaN(value) && 0 <= value && value <= 180 ) 
    this.options.comptonPeakAngle = value;
  else {
    this.options.comptonPeakAngle = 180;  /* default angle is set to 180 degrees */
  }
  this.updateFeatureMarkers();
}

SpectrumChartD3.prototype.setComptonPeaks = function(d) {
  this.options.showComptonPeaks = d;
  if ( d ) {
    this.updateFeatureMarkers();
  }
}

SpectrumChartD3.prototype.setEscapePeaks = function(d) {
  this.options.showEscapePeaks = d;
  if ( d ) {
    this.updateFeatureMarkers();
  }
}

SpectrumChartD3.prototype.setSumPeaks = function(d) {
  this.options.showSumPeaks = d;
  if ( d ) {
    this.updateFeatureMarkers();
  }
}



SpectrumChartD3.prototype.setSearchWindows = function(ranges) {
  var self = this;

  if( !Array.isArray(ranges) || ranges.length===0 ){
    self.searchEnergyWindows = null;
  } else {
    self.searchEnergyWindows = ranges;
    self.searchEnergyWindows.sort( function(l,r){ return l.energy < r.energy }  )
  }

  self.redraw()();
}

//Function that takes regions to draw in a solid fill.
//[{lowerEnergy: 90, upperEnergy: 112, fill: 'rgba(23,53,12,0.1)', hash: 123112319}, ...]
SpectrumChartD3.prototype.setHighlightRegions = function(ranges) {
  var self = this;
  
  if( !Array.isArray(ranges) || ranges.length===0 ){
    self.highlightRegions = null;
    self.vis.selectAll("g.highlight").remove(); //drawHighlightRegions() returns immediatelt if self.highlightRegions is null.
  } else {
    //ToDo add checking that regions have appropriate variables and lowerEnergy is less than upperEnergy
    self.highlightRegions = ranges;
    self.highlightRegions.sort( function(l,r){ return l.lowerEnergy < r.lowerEnergy }  )
  }
  
  self.redraw()();
}


/**
 * -------------- Chart Animation Functions --------------
 */
SpectrumChartD3.prototype.redrawZoomXAnimation = function(targetDomain) {
  var self = this;

  /* Cancel animation if showAnimation option not checked */
  if( !self.options.showAnimation )
    return;

  return function() {
    /* Cancel the animation once reached desired target domain */
    if( self.currentDomain === null || targetDomain === null
        || (self.currentDomain[0] == targetDomain[0] && self.currentDomain[1] == targetDomain[1]) ) {
      //console.log("Time for animation = ", Math.floor(Date.now()) - self.startAnimationZoomTime, " ms");
      self.handleCancelAnimationZoom();
      return;
    }

    /* Use fraction of time elapsed to calculate how far we will zoom in this frame */
    var animationFractionTimeElapsed = Math.min( Math.max((Math.floor(Date.now()) - self.startAnimationZoomTime) / self.options.animationDuration), 1 );

    if( animationFractionTimeElapsed >= 0.999 ){
      self.setXAxisRange( targetDomain[0], targetDomain[1], true );  //do emit range change
      self.handleCancelAnimationZoom();
      self.redraw()();
      /* Update the peak markers */
      self.updateFeatureMarkers(-1);
      return;
    }
    
    /* Set x-axis domain to new values */
    self.setXAxisRange(
      Math.min( self.savedDomain[0] + (animationFractionTimeElapsed * (targetDomain[0] - self.savedDomain[0])), targetDomain[0] ),
      Math.max( self.savedDomain[1] - (animationFractionTimeElapsed * (self.savedDomain[1] - targetDomain[1])), targetDomain[1] ),
      false /* dont emit x-range change. */
    );
    self.currentDomain = self.xScale.domain();

    /* Redraw and request a new animation frame */
    self.redraw()();
    self.zoomAnimationID = requestAnimationFrame(self.redrawZoomXAnimation(targetDomain));
  }
}

SpectrumChartD3.prototype.redrawZoomInYAnimation = function(targetDomain,redraw) {
  var self = this;

  function roundTo3DecimalPlaces(num) { return Math.round(num * 1000) / 1000; }

  /* Cancel animation if showAnimation option not checked */
  if (!self.options.showAnimation) { return; }

  return function() {
    /* Cancel the animation once reached desired target domain */
    if (self.currentDomain == null || targetDomain ==  null || 
      (roundTo3DecimalPlaces(self.currentDomain[0]) == roundTo3DecimalPlaces(targetDomain[0]) && 
        roundTo3DecimalPlaces(self.currentDomain[1]) == roundTo3DecimalPlaces(targetDomain[1]))) {

      console.log("Time for animation = ", Math.floor(Date.now()) - self.startAnimationZoomTime, " ms");
      self.handleCancelAnimationZoom();
      return;
    }

    /* Use fraction of time elapsed to calculate how far we will zoom in this frame */
    var animationFractionTimeElapsed = Math.min( Math.max((Math.floor(Date.now()) - self.startAnimationZoomTime) / self.options.animationDuration), 1 );

    if( animationFractionTimeElapsed >= 0.999 ){
      self.yScale.domain( [targetDomain[0],targetDomain[1]] );
      self.handleCancelAnimationZoom();
      //self.WtEmit(self.chart.id, {name: 'yrangechanged'}, targetDomain[0], targetDomain[1], self.size.width, self.size.height);
      redraw();
      return;
    }
    
    /* Set y-axis domain to new values */
    self.yScale.domain([ 
      Math.max( self.savedDomain[0] - (animationFractionTimeElapsed * (self.savedDomain[0] - targetDomain[0])), targetDomain[0] ),
      Math.min( self.savedDomain[1] + (animationFractionTimeElapsed * (targetDomain[1] - self.savedDomain[1])), targetDomain[1] )
    ]);
    self.currentDomain = self.yScale.domain();

    /* Redraw and request a new animation frame */
    redraw();
    self.zoomAnimationID = requestAnimationFrame(self.redrawZoomInYAnimation(targetDomain, redraw));
  }
}

SpectrumChartD3.prototype.redrawZoomOutYAnimation = function(targetDomain, redraw) {
  var self = this;

  function roundTo3DecimalPlaces(num) { return Math.round(num * 1000) / 1000; }

  /* Cancel animation if showAnimation option not checked */
  if (!self.options.showAnimation) { return; }

  return function() {
    /* Cancel the animation once reached desired target domain */
    if (self.currentDomain == null || targetDomain ==  null || 
      (roundTo3DecimalPlaces(self.currentDomain[0]) == roundTo3DecimalPlaces(targetDomain[0]) && 
        roundTo3DecimalPlaces(self.currentDomain[1]) == roundTo3DecimalPlaces(targetDomain[1]))) {

      //console.log("Time for animation = ", Math.floor(Date.now()) - self.startAnimationZoomTime, " ms");
      self.handleCancelAnimationZoom();
      return;
    }

    /* Use fraction of time elapsed to calculate how far we will zoom in this frame */
    var animationFractionTimeElapsed = Math.min( Math.max((Math.floor(Date.now()) - self.startAnimationZoomTime) / self.options.animationDuration), 1 );

    if( animationFractionTimeElapsed >= 0.999 ){
      self.yScale.domain( [targetDomain[0],targetDomain[1]] );
      self.handleCancelAnimationZoom();
      //self.WtEmit(self.chart.id, {name: 'yrangechanged'}, targetDomain[0], targetDomain[1], self.size.width, self.size.height);
      redraw();
      return;
    }
    
    /* Set y-axis domain to new values */
    self.yScale.domain([ 
      Math.min( self.savedDomain[0] + (animationFractionTimeElapsed * (targetDomain[0] - self.savedDomain[0])), targetDomain[0] ),
      Math.max( self.savedDomain[1] - (animationFractionTimeElapsed * (self.savedDomain[1] - targetDomain[1])), targetDomain[1] )
    ]);
    self.currentDomain = self.yScale.domain();

    /* Redraw and request a new animation frame */
    redraw();
    self.zoomAnimationID = requestAnimationFrame(self.redrawZoomOutYAnimation(targetDomain, redraw));
  }
}

SpectrumChartD3.prototype.setShowAnimation = function(d) {
  this.options.showAnimation = d;
}

SpectrumChartD3.prototype.setAnimationDuration = function(d) {
  this.options.animationDuration = d;
}

SpectrumChartD3.prototype.handleCancelAnimationZoom = function() {
  var self = this;

  /* Cancel the animation frames */
  if (self.zoomAnimationID != null) {
    cancelAnimationFrame(self.zoomAnimationID);
  }

  /* Set animation properties to null */
  self.zoomAnimationID = null;
  self.currentDomain = null;
  self.savedDomain = null;
  self.startAnimationZoomTime = null;
}


/**
 * -------------- X-axis Zoom Functions --------------
 */
SpectrumChartD3.prototype.handleMouseMoveZoomInX = function () {
  var self = this;

  var zoomInXBox = d3.select("#zoomInXBox"),
      zoomInXText = d3.select("#zoomInXText");

  /* Cancel erase peaks mode, we're zooming in */
  self.handleCancelMouseDeletePeak();
  /* Cancel recalibration mode, we're zooming in */
  self.handleCancelMouseRecalibration();

  /* Cancel the zooming in y mode */
  self.handleCancelMouseZoomInY();

  /* Cancel the count gammas mode */
  self.handleCancelMouseCountGammas();

  if (!self.zoominmouse)  return;

  /* Adjust the mouse move position with respect to the bounds of the vis */
  if (self.lastMouseMovePos[0] < 0)
    self.lastMouseMovePos[0] = 0;
  else if (self.lastMouseMovePos[0] > self.size.width)
    self.lastMouseMovePos[0] = self.size.width;

  /* We are now zooming in */
  self.zooming_plot = true;

  /* Restore the zoom-in box */
  if (zoomInXBox.empty()) {
    zoomInXBox = self.vis.append("rect")
      .attr("id", "zoomInXBox")
      .attr("class","leftbuttonzoombox")
      .attr("width", 1 )
      .attr("height", self.size.height)
      .attr("x", self.lastMouseMovePos[0])
      .attr("y", 0)
      .attr("pointer-events", "none");
  }
  
  /* If click-and-drag reaches out of bounds from the plot */
  if (self.lastMouseMovePos[0] < 0 || self.lastMouseMovePos[0] > self.size.width) {
    /* Do something if click and drag reaches out of bounds from plot */
  }


  if( self.lastMouseMovePos[0] < self.zoominmouse[0] ) {      /* If the mouse position is less than the zoombox starting position (zoom-out) */

    /* If we were animating a zoom, cancel that animation */
    self.handleCancelAnimationZoom();

    /* Remove the zoom-in x-axis text, we are zooming out */
    zoomInXText.remove();

    self.zoominaltereddomain = true;
    zoomInXBox.attr("x", self.lastMouseMovePos[0])
      .attr("class","leftbuttonzoomoutbox")
      .attr("height", self.size.height)
      .attr("width", self.zoominmouse[0] - self.lastMouseMovePos[0] );

    /*Do some zooming out */
    var bounds = self.min_max_x_values();
    var xaxismin = bounds[0],
        xaxismax = bounds[1];

    var frac = 4 * (self.zoominmouse[0] - self.lastMouseMovePos[0]) / self.zoominmouse[0];

    if( !isFinite(frac) || isNaN(frac) || frac < 0.0 )
      frac = 0;

    var origdx = self.origdomain[1] - self.origdomain[0],
        maxdx = xaxismax - xaxismin,
        newdx = origdx + frac*(maxdx - origdx);

    var deltadx = newdx - origdx,
    newxmin = Math.max( self.origdomain[0] - 0.5*deltadx, xaxismin ),
    newxmax = Math.min( self.origdomain[1] + 0.5*deltadx, xaxismax );

    /* ToDo: periodically send the xrangechanged signal during zooming out.  Right
       now only sent when mouse goes up.
     */
    self.setXAxisRange(newxmin,newxmax,false);
    self.redraw()();

  } else {  
    /* Set the zoombox (this gets called when current mouse position is greater than where the zoombox started)  */
    if( self.zoominaltereddomain ) {
      self.setXAxisRange( self.origdomain[0], self.origdomain[1], true );
      self.zoominaltereddomain = false;
      zoomInXBox.attr("class","leftbuttonzoombox");
      self.redraw()();
    }

    /* Update the zoomin-box x-position and width */
    zoomInXBox.attr("x", self.zoominmouse[0])
      .attr("width", self.lastMouseMovePos[0] - self.zoominmouse[0] );

    if (self.lastMouseMovePos[0] - self.zoominmouse[0] > 7) {   /* if zoom in box is at least 7px wide, update it */
      if (zoomInXText.empty()) {
        zoomInXText = self.vis.append("text")
          .attr("id", "zoomInXText")
          .attr("class", "chartLineText")
          .attr("y", Number(zoomInXBox.attr("height"))/2)
          .text("Zoom In");
      }

      /* keep zoom in label centered on the box */
      /* zoomInXText.attr("x", Number(zoomInXBox.attr("x")) + (Number(zoomInXBox.attr("width"))/2) - (zoomInXText[0][0].clientWidth/2) ); */
      zoomInXText.attr("x", ((self.zoominmouse[0] + self.lastMouseMovePos[0])/2) - 30);

    } else if (!zoomInXText.empty())       /* delete if zoom in box not wide enough (eg. will not zoom) */
      zoomInXText.remove();

  }
}

SpectrumChartD3.prototype.handleMouseUpZoomInX = function () {
  var self = this;

  if (!self.rawData || !self.rawData.spectra || !self.rawData.spectra.length || !self.zooming_plot)
    return;

  if (self.zooming_plot && self.lastMouseMovePos) { /* Need to add condition if self.lastMouseMovePos exists, or else error is thrown */
    var foreground = self.rawData.spectra[0];

    var lowerchanval = d3.bisector(function(d){return d.x0;}).left(foreground.points,self.xScale.invert(self.zoominmouse[0]),1) - 1;
    var higherchanval = d3.bisector(function(d){return d.x0;}).left(foreground.points,self.xScale.invert(self.lastMouseMovePos[0]),1) - 1;
    
    var yMinAtZoomRange = self.yScale(d3.min(foreground.points.slice(lowerchanval, higherchanval) , function(p) { return p.y; }));
    var yMaxAtZoomRange = self.yScale(d3.max(foreground.points.slice(lowerchanval, higherchanval) , function(p) { return p.y; }));

    /* Get the current mouse position */
    var m = d3.mouse(self.vis[0][0]);

    if( m[0] < self.zoominmouse[0] ) {
      /*we were zooming out, nothing to do here */

    } else {
      m[0] = m[0] < 0 ? 0 : m[0];

      var oldXScale = self.xScale.domain();

      /*This is a big hack, because self.xScale.invert(m[0]) == self.zoominx0 otherwise.  I dont completely understand why! */
      var x0 = self.xScale.invert(self.zoominmouse[0]),
          x1 = self.xScale.invert(m[0]);

      /*require the mouse to have moved at least 6 pixels in x */
      if( m[0] - self.zoominmouse[0] > 7 && self.rawData ) {
          
        var bounds = self.min_max_x_values();
        var mindatax = bounds[0], 
            maxdatax = bounds[1];
        
        /*Make sure the new scale will span at least one bin , if not  */
        /*  make it just less than one bin, centered on that bin. */
        var rawbi = d3.bisector(function(d){return d;}); 
        var lbin = rawbi.left(foreground.x, x0+(x1-x0));
        if( lbin > 1 && lbin < (foreground.x.length-1) && lbin === rawbi.left(foreground.x,x1+(x1-x0)) ) {
          /*This doesnt actually work correctly, it doesnt actually center on the bin, meaning you're always a little off from where you want ... */
          var corx0 = foreground.x[lbin-1];
          var corx1 = foreground.x[lbin];
          var p = 0.01*(corx1-corx0);
          corx0 += p;
          corx1 -= p;
          
          console.log( 'changing x0=' + x0 + ' and x1=' + x1 + " will set domain to " + (x0+(x1-x0)) + " through " + (x1+(x1-x0)) + " m[0]=" + m[0] + " self.zoominmouse[0]=" + self.zoominmouse[0] );
          x0 = Math.max(corx0+(x1-x0), mindatax);
          x1 = Math.min(corx1+(x1-x0), maxdatax);
        }

        
        /* Draw zoom animations if option is checked */
        if( self.options.showAnimation ) {

          /* Cancel any current zoom animations */
          self.handleCancelAnimationZoom();

          /* Start new zoom animation */
          self.currentDomain = self.savedDomain = oldXScale;
          self.zoomAnimationID = requestAnimationFrame(self.redrawZoomXAnimation([x0,x1]));
          self.startAnimationZoomTime = Math.floor(Date.now());
        } else { 
          /* Zoom animation unchecked; draw new x-axis range */
          self.setXAxisRange(x0,x1,true);
          
          self.redraw()();
          
          /* Update the peak markers */
          self.updateFeatureMarkers(-1);
        }   
      }
    }
  }


  self.handleCancelMouseZoomInX();

  self.zooming_plot = false;
}




SpectrumChartD3.prototype.handleCancelMouseZoomInX = function() {
  var self = this;

  var zoomInXBox = d3.select("#zoomInXBox"),
      zoomInXText = d3.select("#zoomInXText");

  /* Delete zoom in box and text */
  zoomInXText.remove();
  zoomInXBox.remove();

  /* Not zooming in plot anymore */
  self.zooming_plot = false;
}


/**
 * -------------- Y-axis Zoom Functions --------------
 */
SpectrumChartD3.prototype.redrawYAxis = function() {
  var self = this;

  return function() {
    self.do_rebin();
    var tx = function(d) { return "translate(" + self.xScale(d) + ",0)"; };
    var stroke = function(d) { return d ? "#ccc" : "#666"; };

    self.yAxisBody.call(self.yAxis);
    self.yAxisBody.selectAll("text").style("cursor", "ns-resize")
        .on("mouseover", function(d) { d3.select(this).style("font-weight", "bold");})
        .on("mouseout",  function(d) { d3.select(this).style("font-weight", null);})
        .on("mousedown.drag",  self.yaxisDrag())
        .on("touchstart.drag", self.yaxisDrag());

    self.drawYTicks();
    
    self.calcLeftPadding( true );

    self.drawXAxisArrows();
    
    self.drawPeaks();
    self.drawRefGammaLines();
    self.updateMouseCoordText();

    self.update(true);

    self.yAxisZoomedOutFully = false;
  }
}

SpectrumChartD3.prototype.setYAxisMinimum = function( minimum ) {
  var self = this;

  const maximum = self.yScale.domain()[0];

  self.yScale.domain([maximum, minimum]);
  self.redrawYAxis()();
}

SpectrumChartD3.prototype.setYAxisMaximum = function( maximum ) {
  var self = this;

  const minimum = self.yScale.domain()[1];

  self.yScale.domain([maximum, minimum]);
  self.redrawYAxis()();
}

SpectrumChartD3.prototype.setYAxisRange = function( minimum, maximum ) {
  var self = this;

  self.yScale.domain([maximum, minimum]);
  self.redrawYAxis()();
}

SpectrumChartD3.prototype.handleMouseMoveZoomInY = function () {
  var self = this;

  /* Set the objects displayed for zooming in the y-axis */
  var zoomInYBox = d3.select("#zoomInYBox"),
      zoomInYText = d3.select("#zoomInYText");

  /* Get the mouse coordinates */
  var m = d3.mouse(self.vis[0][0]);

  /* Cancel the zooming mode */
  self.handleCancelMouseZoomInX();

  /* Cancel erase peaks mode, we're zooming in */
  self.handleCancelMouseDeletePeak();

  /* Cancel recalibration mode, we're zooming in */
  self.handleCancelMouseRecalibration();

  /* Cancel the count gammas mode */
  self.handleCancelMouseCountGammas();

  /* Now zooming in y mode */
  self.zoomingYPlot = true;

  /* Create the reference for the start of the zoom-in (Yaxis) box */
  if (!self.zoomInYMouse)
    self.zoomInYMouse = self.lastMouseMovePos;

  /* Adjust the zoom in y mouse in case user starts dragging from out of bounds */
  if (self.zoomInYMouse[1] < 0)
    self.zoomInYMouse[1] = 0;
  else if (self.zoomInYMouse[1] > self.size.height)
    self.zoomInYMouse[1] = self.size.height;

  if (self.zoomInYMouse[0] < 0 || self.zoomInYMouse[0] > self.size.width) {
    self.handleCancelMouseZoomInY();
    return;
  }

  var height = self.lastMouseMovePos[1] - self.zoomInYMouse[1];

  /* Set the zoom-y box */
  if (zoomInYBox.empty()) {
    zoomInYBox = self.vis.append("rect")
      .attr("id", "zoomInYBox")
      .attr("class","leftbuttonzoombox")
      .attr("width", self.size.width )
      .attr("height", 0)
      .attr("x", 0)
      .attr("y", self.zoomInYMouse[1])
      .attr("pointer-events", "none");
  } else {
    if (height >= 0)  zoomInYBox.attr("height", height);
    else              zoomInYBox.attr("y", self.lastMouseMovePos[1])
                        .attr("height", Math.abs(height));
  }

  if (Math.abs(self.lastMouseMovePos[1] - self.zoomInYMouse[1]) > 10) {   /* if zoom in box is at least 7px wide, update it */
    if (zoomInYText.empty()) {
      zoomInYText = self.vis.append("text")
        .attr("id", "zoomInYText")
        .attr("class", "chartLineText");
      zoomInYText.attr("x", self.size.width/2 - (zoomInYText[0][0].clientWidth/2));

    }

    /* keep zoom in label centered on the box */
    zoomInYText.attr("y", Number(zoomInYBox.attr("y")) + (Number(zoomInYBox.attr("height"))/2) - (zoomInYBox[0][0].clientWidth/2) );

    if (height > 0) {
      zoomInYText.text("Zoom-In on Y-axis");
      zoomInYBox.attr("class", "leftbuttonzoombox");
    }
    else {
      var zoomOutText = "Zoom-out on Y-axis";
      if (-height < 0.05*self.size.height)
        zoomOutText += " x2";
      else if (-height < 0.075*self.size.height)
        zoomOutText += " x4";
      else
        zoomOutText += " full";

      zoomInYText.text(zoomOutText);
      zoomInYBox.attr("class", "leftbuttonzoomoutboxy");
    }

  } else if (!zoomInYText.empty()) {       /* delete if zoom in box not wide enough (eg. will not zoom) */
    zoomInYText.remove();
  }
}

SpectrumChartD3.prototype.handleMouseUpZoomInY = function () {
  var self = this;

  var zoomInYBox = d3.select("#zoomInYBox"),
      zoomInYText = d3.select("#zoomInYText");

  if (zoomInYBox.empty()) {
    self.handleCancelMouseZoomInY();
    return;
  }

  /* Set the y-values for where zoom-in occured */
  var ypix1 = Math.min(Number(zoomInYBox.attr("y")), self.lastMouseMovePos[1]),
      ypix2 = Math.max(Number(zoomInYBox.attr("y")), self.lastMouseMovePos[1]),
      y1 = Math.min(self.yScale.invert(Number(zoomInYBox.attr("y"))), 
                    self.yScale.invert(self.lastMouseMovePos[1]) ),
      y2 = Math.max(self.yScale.invert(Number(zoomInYBox.attr("y"))), 
                    self.yScale.invert(self.lastMouseMovePos[1]) );

  var oldY1 = self.yScale.domain()[0];
  var oldY2 = self.yScale.domain()[1];

  if (self.zoomingYPlot) {
    if (y2 > y1 && Math.abs(ypix2-ypix1) > 10) {  /* we are zooming in */
      if (self.options.showAnimation) {
        self.currentDomain = self.savedDomain = [oldY1, oldY2];

        if (self.zoomAnimationID != null) {
          cancelAnimationFrame(self.zoomAnimationID);
        }
        self.zoomAnimationID = requestAnimationFrame(self.redrawZoomInYAnimation([y2,y1], self.redrawYAxis()));
        self.startAnimationZoomTime = Math.floor(Date.now());

      } else {
        self.yScale.domain([y2,y1]);
        self.redrawYAxis()();
        //self.WtEmit(self.chart.id, {name: 'yrangechanged'}, targetDomain[0], targetDomain[1], self.size.width, self.size.height);
      }
    } else {  /* we are zooming out */

      if (zoomInYText.empty()) {
        self.handleCancelMouseZoomInY();
        return;
      }

      /* Zoom out completely if user dragged up a considerable amount */
      if (zoomInYText.text().endsWith("full")) {

        /* If zoom animations are checked, animate the zoom out */
        if (self.options.showAnimation) {

          /* Cancel previous zoom animation if there was one */
          self.handleCancelAnimationZoom();

          /* Start new zoom animation */
          self.currentDomain = self.savedDomain = [oldY1, oldY2];
          self.zoomAnimationID = requestAnimationFrame(self.redrawZoomOutYAnimation([self.getYAxisDomain()[0],self.getYAxisDomain()[1]], self.redrawYAxis()));
          self.startAnimationZoomTime = Math.floor(Date.now());

        } else { self.redraw()(); }   /* Redraw the chart normally if no zoom animations created */

      } else { /* Zoom out a portion of the full y-axis */

        /* This represents how much of the y-axis we will be zooming out */
        var mult;

        /* Get the mult value here */
        /* For some reason, setting the mult = 1 leads to buggy behavior, so here I set it to x2, x4 respectively */
        if (zoomInYText.text().endsWith("x2"))  mult = 2; 
        else  mult = 4;


        /* Get the old values of the current y-domain */
        var oldY0 = self.yScale.domain()[0],
            oldY1 = self.yScale.domain()[1],
            oldRange = Math.abs(oldY1 - oldY0),
            centroid = oldY0 + 0.5*oldRange;

        /* Values for the minimum and maximum y values */
        var minY, maxY;

        if( !self.rawData || !self.rawData.y ){   /* Manually set the min/max y values */
          minY = 0.1;
          maxY = 3000;

        } else {                                  /* Get the min, max y values from the data */
          let ydomain = self.getYAxisDomain();
          minY = ydomain[1];
          maxY = ydomain[0];
        }

        /* Set the values for the new y-domain */
        var newY0 = Math.max(centroid - mult*oldRange,
                             minY),
            newY1 = Math.min(newY0 + 2*mult*oldRange,
                             maxY);

        /* Accounting for bounds checking, making sure new y domain does not reach beyond min/max values */
        if (newY1 < 0 || newY1 > maxY)
          newY1 = maxY;
        if (newY0 > maxY || newY0 < 0)
          newY0 = minY;

        /* Redraw the newly y-zoomed chart */
        if (!(newY0 == minY && newY1 == maxY)) {

          /* If zoom animations are checked, animate the zoom out */
          if (self.options.showAnimation) {

            /* Cancel previous zoom animation if there was one */
            self.handleCancelAnimationZoom();

            /* Start new zoom animation */
            self.currentDomain = self.savedDomain = [oldY0, oldY1];
            self.zoomAnimationID = requestAnimationFrame(self.redrawZoomOutYAnimation([newY1, newY0], self.redrawYAxis()));
            self.startAnimationZoomTime = Math.floor(Date.now());

          } else { self.yScale.domain([newY1, newY0]); self.redrawYAxis()(); }   /* Redraw the chart normally if no zoom animations created */

        } else {  

          /* If zoom animations are checked, animate the zoom out */
          if (self.options.showAnimation) {

            /* Cancel previous zoom animation if there was one */
            self.handleCancelAnimationZoom();

            /* Start new zoom animation */
            self.currentDomain = self.savedDomain = [oldY0, oldY1];
            self.zoomAnimationID = requestAnimationFrame(self.redrawZoomOutYAnimation([newY1, newY0], self.redraw()));
            self.startAnimationZoomTime = Math.floor(Date.now());

          } else { 
            /* If the new y domain reaches the min/max values and we are still trying to zoom out, */
            /*    then we attempt to zoom out again to capture the initial starting point of the chart */
            self.redraw()();
          }
        }
      }

    }
  }

  /* Clean up objets from zooming in y-axis */
  self.handleCancelMouseZoomInY();
}

SpectrumChartD3.prototype.handleCancelMouseZoomInY = function() {
  var self = this;

  /* Set the objects displayed for zooming in the y-axis */
  var zoomInYBox = d3.select("#zoomInYBox"),
      zoomInYText = d3.select("#zoomInYText");

  /* Not zooming in y anymore */
  self.zoomingYPlot = false;
  self.zoomInYMouse = null;

  /* Delete zoom box and text */
  zoomInYBox.remove();
  zoomInYText.remove();
}

SpectrumChartD3.prototype.handleTouchMoveZoomInY = function() {
  var self = this;

  if (!self.touchesOnChart)
    return;

  /* Cancel delete peaks mode */
  self.handleCancelTouchDeletePeak();

  /* Cancel the create peaks mode */
  self.handleCancelTouchPeakFit();

  /* Cancel the count gammas mode */
  self.handleCancelTouchCountGammas();

  var t = d3.touches(self.vis[0][0]);

  var keys = Object.keys(self.touchesOnChart);

  if (keys.length !== 2)
    return;
  if (t.length !== 2)
    return;

  var zoomInYTopLine = d3.select("#zoomInYTopLine");
  var zoomInYBottomLine = d3.select("#zoomInYBottomLine");
  var zoomInYText = d3.select("#zoomInYText");

  var touch1 = self.touchesOnChart[keys[0]];
  var touch2 = self.touchesOnChart[keys[1]];
  var adx1 = Math.abs( touch1.startX - touch2.startX );
  var adx2 = Math.abs( touch1.pageX  - touch2.pageX );
  var ady1 = Math.abs( touch1.startY - touch2.startY );
  var ady2 = Math.abs( touch1.pageY  - touch2.pageY );
  var ddx = Math.abs( adx2 - adx1 );
  var ddy = Math.abs( ady2 - ady1 );
  var areVertical = (adx2 > ady2);

  if (!touch1.visY)
    touch1.visY = t[0][1];
  if (!touch2.visY)
    touch2.visY = t[1][1];

  var topTouch = touch1.pageY < touch2.pageY ? touch1 : touch2;
  var bottomTouch = topTouch == touch1 ? touch2 : touch1;

  if (zoomInYTopLine.empty()) {
    zoomInYTopLine = self.vis.append("line")
      .attr("id", "zoomInYTopLine")
      .attr("class", "mouseLine")
      .attr("x1", 0)
      .attr("x2", self.size.width)
      .attr("y1", topTouch.visY)
      .attr("y2", topTouch.visY)
      .attr("count", self.yScale.invert(topTouch.visY));
  }

  if (zoomInYBottomLine.empty()) {
    zoomInYBottomLine = self.vis.append("line")
      .attr("id", "zoomInYBottomLine")
      .attr("class", "mouseLine")
      .attr("x1", 0)
      .attr("x2", self.size.width)
      .attr("y1", bottomTouch.visY)
      .attr("y2", bottomTouch.visY)
      .attr("count", self.yScale.invert(bottomTouch.visY));
  }

  if (zoomInYText.empty()) {
    zoomInYText = self.vis.append("text")
      .attr("id", "zoomInYText")
      .attr("class", "mouseLineText");
  }

  zoomInYText.text(function() {
    if (topTouch.visY > topTouch.startY && bottomTouch.visY < bottomTouch.startY)
      return "Zoom-Out on Y-axis";
    else if (topTouch.visY == topTouch.startY && bottomTouch.visY == bottomTouch.startY)
      return "";
    else
      return "Zoom-In on Y-axis";
  });

  zoomInYText.attr("x", self.size.width/2 - Number(zoomInYText[0][0].clientWidth)/2)
    .attr("y", Number(topTouch.startY) + (bottomTouch.startY - topTouch.startY)/2);
}

SpectrumChartD3.prototype.handleTouchEndZoomInY = function() {
  var self = this;

  var zoomInYTopLine = d3.select("#zoomInYTopLine");
  var zoomInYBottomLine = d3.select("#zoomInYBottomLine");
  var zoomInYText = d3.select("#zoomInYText");

  if (zoomInYTopLine.empty() || zoomInYBottomLine.empty()) {
    self.handleTouchCancelZoomInY();
    return;
  }
  /* Set the y-values for where zoom-in occured */
  var ypix1 = Number(zoomInYTopLine.attr("y1")),
      ypix2 = Number(zoomInYBottomLine.attr("y1")),
      y1 = Number(zoomInYTopLine.attr("count")),
      y2 = Number(zoomInYBottomLine.attr("count"));

  console.log(y1, y2);
  /*
  This function is a similar method to the redraw function, except without certain actions
  taken out to only acount for redrawing the the zoomed chart by y-axis.
  */
  function redrawYAxis() {
    self.do_rebin();
    var tx = function(d) { return "translate(" + self.xScale(d) + ",0)"; };
    var stroke = function(d) { return d ? "#ccc" : "#666"; };

    self.yAxisBody.call(self.yAxis);
    self.yAxisBody.selectAll("text").style("cursor", "ns-resize")
        .on("mouseover", function(d) { d3.select(this).style("font-weight", "bold");})
        .on("mouseout",  function(d) { d3.select(this).style("font-weight", null);})
        .on("mousedown.drag",  self.yaxisDrag())
        .on("touchstart.drag", self.yaxisDrag());

    self.drawYTicks();
    
    self.calcLeftPadding( true );

    self.drawXTicks();

    self.drawXAxisArrows();
    
    self.drawPeaks();
    self.drawRefGammaLines();
    self.updateMouseCoordText();

    self.update();

    self.yAxisZoomedOutFully = false;
  }

  if (Math.abs(ypix2-ypix1) > 10) {  /* we are zooming in */
    if (zoomInYText.text().includes("Zoom-In")) {
      self.yScale.domain([y1,y2]);
      redrawYAxis();

    } else if (zoomInYText.text().includes("Zoom-Out")) {
        console.log("zooming out!");
        self.redraw()();
    }
  }
  self.handleTouchCancelZoomInY();
}

SpectrumChartD3.prototype.handleTouchCancelZoomInY = function() {
  var self = this;

  var zoomInYTopLine = d3.select("#zoomInYTopLine");
  var zoomInYBottomLine = d3.select("#zoomInYBottomLine");
  var zoomInYText = d3.select("#zoomInYText");

  zoomInYTopLine.remove();
  zoomInYBottomLine.remove();
  zoomInYText.remove();

  self.zoomInYPinch = null;
}


/**
 * -------------- Energy Recalibration Functions --------------
 */
SpectrumChartD3.prototype.handleMouseMoveRecalibration = function() {
  var self = this;

  /* Clear the zoom, we're recalibrating the chart */
  self.handleCancelMouseZoomInX();

  /* Cancel erase peaks mode, we're recalibrating the chart */
  self.handleCancelMouseDeletePeak();

  /* Cancel the zooming in y mode */
  self.handleCancelMouseZoomInY();

  /* Cancel the count gammas mode */
  self.handleCancelMouseCountGammas();

  if (!self.recalibrationMousePos)
    return;
  if (!self.rawData || !self.rawData.spectra || !self.rawData.spectra.length) 
    return;

  /* Adjust the mouse move position with respect to the bounds of the vis */
  if (self.lastMouseMovePos[0] < 0)
    self.lastMouseMovePos[0] = 0;
  else if (self.lastMouseMovePos[0] > self.size.width)
    self.lastMouseMovePos[0] = self.size.width;

  /* Set the line objects to be referenced */
  var recalibrationStartLine = d3.select("#recalibrationStartLine"),
      recalibrationText = d3.select("#recalibrationText"),
      recalibrationMousePosLines = d3.select("#recalibrationMousePosLines");

  var recalibrationG = d3.select("#recalibrationG");
  var recalibrationPeakVis = d3.select("#recalibrationPeakVis");

  /* Set the line that symbolizes where user initially began right-click-and-drag */
  //.mouseLine      { font-size: 0.8em; stroke-width: 2; }
  //.secondaryMouseLine { font-size: 0.8em; stroke-width: 1; }
  
  //ToDo: get exiscolor
  let axiscolor = 'black'
  if (recalibrationStartLine.empty()) {
    
    const tickElement = document.querySelector('.tick');
    const tickStyle = tickElement ? getComputedStyle(tickElement) : null;
    axiscolor = tickStyle && tickStyle.stroke ? tickStyle.stroke : 'black';
    
    recalibrationStartLine = self.vis.append("line")
      .attr("id", "recalibrationStartLine")
      .attr("class", "mouseLine")
      .attr("x1", self.recalibrationMousePos[0])
      .attr("x2", self.recalibrationMousePos[0])
      .attr("y1", 0)
      .attr("y2", self.size.height)
      .attr("stroke",axiscolor);
  }

  if (recalibrationText.empty()) {                       /* Right-click-and-drag text to say where recalibration ranges are */
    //ToDo: make sure this text same color as chart text.  Also, put on translucent background
    recalibrationText = self.vis.append("text")
      .attr("id", "recalibrationText")
      .attr("class", "mouseLineText")
      .attr("x", self.recalibrationMousePos[0] + 5 /* As padding from the starting line */ )
      .attr("y", self.size.height/2)
      .text("Recalibrate data from " + self.xScale.invert(self.lastMouseMovePos[0]).toFixed(2) + " to " + self.xScale.invert(self.lastMouseMovePos[0]).toFixed(2) + " keV");

  } else   /* Right-click-and-drag text already visible in vis, so just update it */
    recalibrationText.text( "Recalibrate data from " + self.xScale.invert(recalibrationStartLine.attr("x1")).toFixed(2) + " to " + self.xScale.invert(self.lastMouseMovePos[0]).toFixed(2) + " keV" )
  

  // Draw the distance lines from the right-click-and-drag line to mouse position
/*
  if (!self.recalibrationDistanceLines) {
    var distanceLine;
    self.recalibrationDistanceLines = [];

    var lineSpacing = self.size.height / 5;

    //Create 4 lines that draw from the right-click-and-drag initial starting point to where the mouse is
    for (i = 0; i < 4; i++) {
      distanceLine = self.vis.append("line")
                            .attr("class", "secondaryMouseLine")
                            .attr("x1", recalibrationStartLine.attr("x1"))
                            .attr("x2", self.lastMouseMovePos[0])
                            .attr("y1", lineSpacing)
                            .attr("y2", lineSpacing);
       //This is to add the the arrowhead end to the distance lines
      var arrow = self.vis.append('svg:defs')
        .attr("id", "recalibrationArrowDef")
        .append("svg:marker")
          .attr("id", "rightClickDragArrow")
          .attr('class', 'xaxisarrow')
          .attr("refX", 0)
          .attr("refY", 7)
          .attr("markerWidth", 25)
          .attr("markerHeight", 25)
          .attr("orient", 0)
          .append("path")
            .attr("d", "M2,2 L2,13 L8,7 L2,2")
            .style("stroke", "black");

      distanceLine.attr("marker-end", "url(#rightClickDragArrow)");

      self.recalibrationDistanceLines.push(distanceLine);
      lineSpacing += self.size.height / 5;
    }

  } else {    // Distance lines have already been drawn
    for (i = 0; i < self.recalibrationDistanceLines.length; i++) {
      var x2 = self.lastMouseMovePos[0];

      // If mouse position is to the left of the right-click-and-drag line
      if (self.lastMouseMovePos[0] < recalibrationStartLine.attr("x1")) {
        self.recalibrationDistanceLines[i].attr("x2", x2);     //Adjust the x-position of the line

        d3.selectAll("#rightClickDragArrow > path").each(function(){            //Flip the arrowhead to face towards the negative x-axis
          d3.select(this).attr("transform", "translate(8,14) rotate(180)");
        });
      }
      else {
        //To adjust for the length of the line with respect to its arrowhead
        if (self.recalibrationDistanceLines[i].attr("x2") > 0)
          x2 -= 8;  //Minus 8 to account for the arrow width connected to the line
        else
          x2 = 0;

        // Adjust the x-position of the line
        self.recalibrationDistanceLines[i].attr("x2", x2);

        // Un-flip the arrowhead (if it was flipped) back to pointing towards the positive x-axis
        d3.selectAll("#rightClickDragArrow > path").each(function(){
          d3.select(this).attr("transform", null);
        });
      }
    }
  }
 */

  /* Draw the line to represent the mouse position for recalibration */
  if (recalibrationMousePosLines.empty())
    recalibrationMousePosLines = self.vis.append("line")
      .attr("id", "recalibrationMousePosLines")
      .attr("y1", 0)
      .attr("y2", self.size.height)
      .attr("stroke",axiscolor)
      .style("opacity", 0.75)
      .attr("stroke-width",0.5);
      ;
   
  /* Update the mouse position line for recalibration */
  recalibrationMousePosLines.attr("x1", self.lastMouseMovePos[0])
    .attr("x2", self.lastMouseMovePos[0]);

  /* Add the background for the recalibration animation */
  if (recalibrationG.empty()) {
    recalibrationG = self.vis.append("g")
      .attr("id", "recalibrationG")
      .attr("clip-path", "url(#clip" + this.chart.id + ")");
  }

  /* Add the foreground, background, and secondary lines for recalibration animation */
  for (var i = 0; i < ((self.rawData && self.rawData.spectra) ? self.rawData.spectra.length : 0); ++i) {
    var spectrum = self.rawData.spectra[i];
    var recalibrationLine = d3.select("#recalibrationLine"+i);

    if (recalibrationLine.empty() && self['line'+i]) {
      recalibrationLine = recalibrationG.append("path")
        .attr("id", "recalibrationLine"+i)
        .attr("class", "rline")
        .attr("stroke", spectrum.lineColor ? spectrum.lineColor : 'black')
        .attr("d", self['line'+i](spectrum.points));
    }
  }

  if (recalibrationPeakVis.empty() && self.peakVis) {
    recalibrationPeakVis = recalibrationG.append("g")
      .attr("id", "recalibrationPeakVis")
      .attr("class", "peakVis")
      .attr("transform","translate(0,0)")
      .attr("clip-path", "url(#clip" + this.chart.id + ")");

    self.peakVis.selectAll("path").each(function() {
      path = d3.select(this);
      recalibrationPeakVis.append("path")
        .attr("class", path.attr("class"))
        .attr("d", path.attr("d"))
        .attr("fill-opacity", 0.4)
        .style("fill", path.style("fill"))
        ;
    });
  }

  recalibrationPeakVis.attr("transform", "translate(" + (self.lastMouseMovePos[0] - self.recalibrationMousePos[0]) + ",0)");

  /* Move the foreground, background, and secondary lines for recalibration animation with relation to mouse position */
  for (var i = 0; i < ((self.rawData && self.rawData.spectra) ? self.rawData.spectra.length : 0); ++i) {
    var recalibrationLine = d3.select("#recalibrationLine"+i);

    if (!recalibrationLine.empty())
      recalibrationLine.attr("transform", "translate(" + (self.lastMouseMovePos[0] - self.recalibrationMousePos[0]) + ",0)");
  }
}

SpectrumChartD3.prototype.handleMouseUpRecalibration = function() {
  var self = this;

  /* Handle Right-click-and-drag (for recalibrating data) */
  if (self.recalibrationMousePos) {

    /* Emit the signal here */
    if (self.isRecalibrating) {
      console.log("Emit RECALIBRATION SIGNAL from x0 = ", self.xScale(self.recalibrationStartEnergy[0]), 
        "(", self.recalibrationStartEnergy[0], " keV) to x1 = ", 
        self.lastMouseMovePos[0], "(", 
        self.xScale.invert(self.lastMouseMovePos[0]), " keV)");
      self.WtEmit(self.chart.id, {name: 'rightmousedragged'}, self.recalibrationStartEnergy[0], self.xScale.invert(self.lastMouseMovePos[0]));
    }

    self.handleCancelMouseRecalibration();
  }

  /* User is not right-click-and-dragging any more, so set this to null */
  if (self.isRecalibrating)
    self.recalibrationMousePos = null;
}

SpectrumChartD3.prototype.handleCancelMouseRecalibration = function() {
  var self = this;

  var recalibrationStartLine = d3.select("#recalibrationStartLine"),
      recalibrationText = d3.select("#recalibrationText"),
      recalibrationMousePosLines = d3.select("#recalibrationMousePosLines");

  var recalibrationG = d3.select("#recalibrationG");
  var recalibrationPeakVis = d3.select("#recalibrationPeakVis");

  /* Remove the right-click-and-drag initial starting point line */
  recalibrationStartLine.remove();

  /* Remove the right-click-and-drag text */
  recalibrationText.remove()

  /* Remove the peak vis */
  recalibrationPeakVis.remove();

  /* Remove all the arrow defs created */
  d3.selectAll("#recalibrationArrowDef").each(function(){
    this.remove();
  });

  /* Remove the right-click-and-drag end-point line */
  /*
  if (self.recalibrationDistanceLines) {
    for (i = 0; i < self.recalibrationDistanceLines.length; i++) {
      self.recalibrationDistanceLines[i].remove();
    }
    self.recalibrationDistanceLines = null;
  }
   */

  /* Remove the right-click-and-drag mouse line */
  recalibrationMousePosLines.remove();

  self.isRecalibrating = false;

  /* /* User is not right-click-and-dragging any more, so set this to null */
  if (self.isRecalibrating)
    self.recalibrationMousePos = null;

  recalibrationG.remove();
}


/**
 * -------------- Delete Peak Functions --------------
 */
SpectrumChartD3.prototype.handleMouseMoveDeletePeak = function() {
  var self = this;

  var deletePeaksBox = d3.select("#deletePeaksBox"),
      deletePeaksText = d3.select("#deletePeaksText");

  d3.event.preventDefault();
  d3.event.stopPropagation();

  /* Cancel the zooming mode */
  self.handleCancelMouseZoomInX();

  /* Cancel the recalibration mode */
  self.handleCancelMouseRecalibration();

  /* Cancel the zooming in y mode */
  self.handleCancelMouseZoomInY();

  /* Cancel the count gammas mode */
  self.handleCancelMouseCountGammas();

  self.handleCancelRoiDrag();

  self.erasePeakFitReferenceLines();
  

  if (!self.deletePeaksMouse)
    return;

  /* Adjust the mouse move position with respect to the bounds of the vis */
  if (self.lastMouseMovePos[0] < 0)
    self.lastMouseMovePos[0] = 0;
  else if (self.lastMouseMovePos[0] > self.size.width)
    self.lastMouseMovePos[0] = self.size.width;

  /* Create the erase-peaks range box and text  */
  if (deletePeaksBox.empty()) {
    deletePeaksBox = self.vis.append("rect")
      .attr("id", "deletePeaksBox")
      .attr("class","deletePeaksBox")
      .attr("width", Math.abs( self.deletePeaksMouse[0] - self.lastMouseMovePos[0] ))
      .attr("height", self.size.height)
      .attr("y", 0);

    deletePeaksText = self.vis.append("text")
      .attr("id", "deletePeaksText")
      .attr("class", "deletePeaksText")
      .attr("y", Number(deletePeaksBox.attr("height"))/2)
      .text("Will Erase Peaks In Range");

  } else {  /* Erase-peaks range box has already been created, update it */


    /* Adjust the width of the erase peaks box */
    deletePeaksBox.attr("width", Math.abs( self.deletePeaksMouse[0] - self.lastMouseMovePos[0] ));
  }

  deletePeaksBox.attr("x", self.lastMouseMovePos[0] < self.deletePeaksMouse[0] ? self.lastMouseMovePos[0] : self.deletePeaksMouse[0])

  /* Move the erase peaks text in the middle of the erase peaks range box */
  deletePeaksText.attr("x", Number(deletePeaksBox.attr("x")) + (Number(deletePeaksBox.attr("width"))/2) - 40 );
}

SpectrumChartD3.prototype.handleMouseUpDeletePeak = function() {
  var self = this;

  var deletePeaksBox = d3.select("#deletePeaksBox"),
      deletePeaksText = d3.select("#deletePeaksText");

  var deletePeaksRange;

  try {
    deletePeaksRange = [ 
      Math.min(self.xScale.invert(Number(deletePeaksBox.attr("x"))), self.xScale.invert(Number(deletePeaksBox.attr("x")) + Number(deletePeaksBox.attr("width")))), 
      Math.max(self.xScale.invert(Number(deletePeaksBox.attr("x"))), self.xScale.invert(Number(deletePeaksBox.attr("x")) + Number(deletePeaksBox.attr("width")))) 
      ];

    console.log("Emit ERASE PEAKS SIGNAL FROM ", deletePeaksRange[0], "keV to ", deletePeaksRange[1], " keV" );
    self.WtEmit(self.chart.id, {name: 'shiftkeydragged'}, deletePeaksRange[0], deletePeaksRange[1]);

  } catch (TypeError) { /* For some reason, a type error is (seldom) returned when trying to access "x" attribute of deletePeaksBox, doesn't affect overall functionality though */
    return;
  }

  self.handleCancelMouseDeletePeak();
}

SpectrumChartD3.prototype.handleCancelMouseDeletePeak = function() {
  var self = this;

  var deletePeaksBox = d3.select("#deletePeaksBox"),
      deletePeaksText = d3.select("#deletePeaksText");

  /* Delete the erase peaks box since we are not erasing peaks anymore */
  deletePeaksBox.remove();

  /* Delete the erase peaks text since we are not erasing peaks anymore */
  deletePeaksText.remove();

  /* We are not erasing peaks anymore */
  self.isDeletingPeaks = false;
}

SpectrumChartD3.prototype.handleTouchMoveDeletePeak = function() {
  var self = this;

  var t = self.deletePeaksTouches;

  if (t.length !== 2) {
    self.handleCancelTouchDeletePeak();
    return;
  }

  /* Cancel the count gammas mode */
  self.handleCancelTouchCountGammas();

  /* Cancel the create peaks mode */
  self.handleCancelTouchPeakFit();

  /* Cancel the zoom-in y mode */
  self.handleTouchCancelZoomInY();

  var deletePeaksBox = d3.select("#deletePeaksBox"),
      deletePeaksText = d3.select("#deletePeaksText");

  var leftTouch = t[0][0] < t[1][0] ? t[0] : t[1],
      rightTouch = leftTouch === t[0] ? t[1] : t[0];

  var leftTouchX = Math.min(leftTouch[0], self.xScale.range()[1]);
  var rightTouchX = Math.min(rightTouch[0], self.xScale.range()[1]);
  var width = Math.abs( rightTouchX - leftTouchX );

  if (leftTouchX > self.xScale.invert(self.xScale.domain()[1])) {
    self.handleCancelTouchDeletePeak();
    return;
  }

  /* Create the erase-peaks range box and text  */
  if (deletePeaksBox.empty()) {
    deletePeaksBox = self.vis.append("rect")
      .attr("id", "deletePeaksBox")
      .attr("class","deletePeaksBox")
      .attr("height", self.size.height)
      .attr("y", 0);

    deletePeaksText = self.vis.append("text")
      .attr("id", "deletePeaksText")
      .attr("class", "deletePeaksText")
      .attr("y", Number(deletePeaksBox.attr("height"))/2);

  }

  /* Adjust the positioning and width of the delete peaks box */
  deletePeaksBox.attr("x", leftTouchX)
    .attr("width", width);


  /* Move the erase peaks text in the middle of the erase peaks range box */
  deletePeaksText.text(width > 0 ? "Will Erase Peaks In Range" : "");
  deletePeaksText.attr("x", Number(deletePeaksBox.attr("x")) + (Number(deletePeaksBox.attr("width"))/2) - Number(deletePeaksText[0][0].clientWidth)/2 );
}

SpectrumChartD3.prototype.handleTouchEndDeletePeak = function() {
  var self = this;

  var deletePeaksBox = d3.select("#deletePeaksBox"),
      deletePeaksText = d3.select("#deletePeaksText");

  var deletePeaksRange;

  try {
    deletePeaksRange = [ 
      Math.min(self.xScale.invert(Number(deletePeaksBox.attr("x"))), self.xScale.invert(Number(deletePeaksBox.attr("x")) + Number(deletePeaksBox.attr("width")))), 
      Math.max(self.xScale.invert(Number(deletePeaksBox.attr("x"))), self.xScale.invert(Number(deletePeaksBox.attr("x")) + Number(deletePeaksBox.attr("width")))) 
      ];

    console.log("Emit ERASE PEAKS SIGNAL FROM ", deletePeaksRange[0], "keV to ", deletePeaksRange[1], " keV" );
    self.WtEmit(self.chart.id, {name: 'shiftkeydragged'}, deletePeaksRange[0], deletePeaksRange[1]);

  } catch (TypeError) { /* For some reason, a type error is (seldom) returned when trying to access "x" attribute of deletePeaksBox, doesn't affect overall functionality though */
    return;
  }

  self.handleCancelTouchDeletePeak();
}

SpectrumChartD3.prototype.handleCancelTouchDeletePeak = function() {
  var self = this;

  var deletePeaksBox = d3.select("#deletePeaksBox"),
      deletePeaksText = d3.select("#deletePeaksText");

  /* Delete the erase peaks box since we are not erasing peaks anymore */
  deletePeaksBox.remove();

  /* Delete the erase peaks text since we are not erasing peaks anymore */
  deletePeaksText.remove();

  /* We are not deleting peaks anymore, delete the touches */
  self.deletePeaksTouches = null;
}


/**
 * -------------- Count Gammas Functions --------------
 */

SpectrumChartD3.prototype.gammaIntegral = function(spectrum, lowerX, upperX) {
  let self = this;
  var sum = 0.0;
  
  if( !spectrum || !spectrum.x || !spectrum.y )
    return sum;
  
  var bounds = self.min_max_x_values();
  var maxX = bounds[1];
  var minX = bounds[0];
  
  lowerX = Math.min( maxX, Math.max(lowerX, minX) );
  upperX = Math.max( minX, Math.min(upperX, maxX) );
  
  if (lowerX == upperX)
    return sum;
  
  if (lowerX > upperX) {  /* swap the two values */
    upperX = [lowerX, lowerX = upperX][0];
  }
  
  var maxChannel = spectrum.x.length - 1;
  var lowerChannel = d3.bisector(function(d){return d;}).left(spectrum.x,lowerX,1) - 1;
  var upperChannel = d3.bisector(function(d){return d;}).left(spectrum.x,upperX,1) - 1;
  
  var lowerLowEdge = spectrum.x[lowerChannel];
  var lowerBinWidth = lowerChannel < maxChannel ? spectrum.x[lowerChannel+1] - spectrum.x[lowerChannel]
                                                : spectrum.x[lowerChannel] - spectrum.x[lowerChannel-1];
  var lowerUpEdge = lowerLowEdge + lowerBinWidth;
  
  if (lowerChannel === upperChannel) {
    var frac = (upperX - lowerX) / lowerBinWidth;
    //console.log("lowerChannel == upper channel, counts = ", frac * spectrum.y[lowerChannel]);
    return frac * spectrum.y[lowerChannel];
  }
  
  var fracLowBin = (lowerUpEdge - lowerX) / lowerBinWidth;
  sum += fracLowBin * spectrum.y[lowerChannel];
  
  var upperLowEdge = spectrum.x[upperChannel];
  var upperBinWidth = upperChannel < maxChannel ? spectrum.x[upperChannel+1] - spectrum.x[upperChannel]
                                                : spectrum.x[upperChannel] - spectrum.x[upperChannel-1];
  var fracUpBin = (upperX - upperLowEdge) / upperBinWidth;
  sum += fracUpBin * spectrum.y[upperChannel];
  
  
  for (var channel = lowerChannel + 1; channel < upperChannel; channel++) {
    sum += spectrum.y[channel];
  }
  
  return sum;
}

/**
 \TODO: This function is really similar to SpectrumChartD3.prototype.handleTouchMoveCountGammas; they should be compined as much as possible.
 */
SpectrumChartD3.prototype.handleMouseMoveCountGammas = function() {
  var self = this

  d3.event.preventDefault();
  d3.event.stopPropagation();

  /* Cancel the zooming mode */
  self.handleCancelMouseZoomInX();

  /* Cancel the recalibration mode */
  self.handleCancelMouseRecalibration();

  /* Cancel the zooming in y mode */
  self.handleCancelMouseZoomInY();

  /* Cancel the delete peak mode */
  self.handleCancelMouseDeletePeak();

  if (!self.countGammasMouse || !self.lastMouseMovePos || !self.rawData || !self.rawData.spectra || !self.rawData.spectra.length)
    return;
  
  function needsDecimal(num) {
    return num % 1 != 0;
  }

  /* Adjust the mouse move position with respect to the bounds of the vis */
  if (self.lastMouseMovePos[0] < 0)
    self.lastMouseMovePos[0] = 0;
  else if (self.lastMouseMovePos[0] > self.size.width)
    self.lastMouseMovePos[0] = self.size.width;

  let startx = self.countGammasMouse[0];
  let nowx = self.lastMouseMovePos[0];
    
    
  var countGammasBox = d3.select("#countGammasBox"),
      countGammasText = d3.select("#countGammasText"),
      countGammaRangeText = d3.select("#countGammaRangeText"),
      sigmaCount = d3.select("#sigmaCount");
  var countGammasRange = [ 
      Number(self.xScale.invert(Number(startx).toFixed(1))),
      Number(self.xScale.invert(Number(nowx).toFixed(1)))
  ];

  /* Create the yellow box and text associated with it */
  if (countGammasBox.empty()) { 
    countGammasBox = self.vis.append("rect")
      .attr("id", "countGammasBox")
      .attr("width", Math.abs( startx - nowx ))
      .attr("height", self.size.height)
      .attr("y", 0);

  } else {  /* Adjust the width of the erase peaks box */
    countGammasBox.attr("width", Math.abs( startx - nowx ));
  }
  if (countGammasText.empty()) {
    countGammasText = self.vis.append("text")
      .attr("id", "countGammasText")
      .attr("class", "countGammasText")
      .attr("y", Number(countGammasBox.attr("height"))/2)
      .text("Gamma Counts");
  }
  var ypos = Number(countGammasBox.attr("height"))/2 + 15;   /* signifies the y-position of the text displayed */

  /* Mouse position to the left of initial starting point of count gammas box */
  if (nowx <= startx) {
    d3.selectAll('.asterickText').remove();
    countGammasBox.attr("class", "deletePeaksBox")
      .attr("x", nowx);
    countGammasText.text("Will remove gamma count range");

    /* Move the count gammas text in the middle of the count gammas box */
    countGammasText.attr("x", Number(countGammasBox.attr("x")) + (Number(countGammasBox.attr("width"))/2) - 30 /*Number(countGammasText[0][0].clientWidth)/2*/ );

    /* Remove the counts text (we will not be counting gammas) */
    self.rawData.spectra.forEach(function(spectrum) {
      d3.select('#Spectrum-' + spectrum.id + 'CountsText').remove();
      d3.select('#Spectrum-' + spectrum.id + 'AsterickText').remove();
      d3.select("#asterickText"+i).remove();
    });
    countGammaRangeText.remove();
    sigmaCount.remove();

    return;

  } else {
    countGammasBox.attr("class", "countGammasBoxForward")
      .attr("x", nowx < startx ? nowx : startx);
    countGammasText.text("Gamma Counts");

    if (countGammaRangeText.empty())
      countGammaRangeText = self.vis.append("text")
        .attr("id", "countGammaRangeText")
        .attr("class", "countGammasText")
        .attr("y", ypos);


    countGammaRangeText.text((needsDecimal(countGammasRange[0]) ? countGammasRange[0].toFixed(1) : countGammasRange[0].toFixed()) + 
                              " to " + 
                              (needsDecimal(countGammasRange[1]) ? countGammasRange[1].toFixed(1) : countGammasRange[1].toFixed()) + " keV");
    countGammaRangeText.attr("x", Number(countGammasBox.attr("x")) + (Number(countGammasBox.attr("width"))/2) - 30 /*Number(countGammaRangeText[0][0].clientWidth)/2*/);
  }
  ypos += 15;

  /* Move the count gammas text in the middle of the count gammas box */
  countGammasText.attr("x", Number(countGammasBox.attr("x")) + (Number(countGammasBox.attr("width"))/2) - 30 /*Number(countGammasText[0][0].clientWidth)/2*/ );

  /* Display the count gammas text for all the spectrum */
  var nforeground, nbackground, backSF;
  var nsigma = 0, isneg;
  var asterickText = "";
  var rightPadding = 50;
  var specialScaleSpectras = [];
  self.rawData.spectra.forEach(function(spectrum, i) {   /* TODO: May need to change processing of */
    if (!spectrum)
      return;

    /* Get information from the spectrum */
    var spectrumSelector = 'Spectrum-' + spectrum.id;
    var spectrumCountsText = d3.select("#" + spectrumSelector + "CountsText");
    var spectrumScaleFactor = spectrum.yScaleFactor;
    var nspectrum = self.gammaIntegral(spectrum, countGammasRange[0], countGammasRange[1]);
    var spectrumGammaCount = Number((spectrumScaleFactor * nspectrum).toFixed(2));
    var countsText;

    /* Save information for the foreground and background (for sigma comparison) */
    if (spectrum.type === self.spectrumTypes.FOREGROUND)
      nforeground = nspectrum;
    else if (spectrum.type === self.spectrumTypes.BACKGROUND) {
      nbackground = nspectrum;
      backSF = spectrumScaleFactor;
    }

    /* Get the text to be displayed from the spectrum information */
    if (spectrumScaleFactor != null && spectrumScaleFactor !== -1)
      countsText = spectrum.title + ": " + (needsDecimal(spectrumGammaCount) ? spectrumGammaCount.toFixed(2) : spectrumGammaCount.toFixed());
    if (spectrumScaleFactor != 1) {
      asterickText += "*";
      if (countsText)
        countsText += asterickText;
      specialScaleSpectras.push(asterickText + "scaled by " + 
        (needsDecimal(spectrumScaleFactor) ? spectrumScaleFactor.toFixed(3) : spectrumScaleFactor.toFixed()) + " from actual");
    }

    /* Output the count gammas information to the chart */
    if (countsText) {
      if (spectrumCountsText.empty())
        spectrumCountsText = self.vis.append("text")
          .attr("id", spectrumSelector + "CountsText")
          .attr("class", "countGammasText")
          .attr("y", ypos);
      spectrumCountsText.text(countsText); 
      spectrumCountsText.attr("x", Number(countGammasText.attr("x")) - rightPadding );
      ypos += 15;

    } else {
      spectrumCountsText.remove();
    }
  });

  /* Get proper information for foreground-background sigma comparison */
  if (nforeground && nbackground && backSF) {
    const backSigma = backSF * Math.sqrt(nbackground);
    const sigma = Math.sqrt( backSigma*backSigma + nforeground );  //uncerFore = sqrt(nforeground) since foreground always scaled by 1.0
    nsigma = backSigma == 0 ? 0 : (Number((Math.abs(nforeground - backSF*nbackground) / sigma).toFixed(3)));
    isneg = ((backSF*nbackground) > nforeground);
  }

  /* Output foreground-background sigma information if it is available */
  if (nsigma > 0) {
    if (sigmaCount.empty())
      sigmaCount = self.vis.append("text")
        .attr("id", "sigmaCount")
        .attr("class", "countGammasText")
        .attr("y", ypos);

    sigmaCount.attr("x", Number(countGammasText.attr("x")) - rightPadding + 10)
      .text("Foreground is " + (needsDecimal(nsigma) ? nsigma.toFixed(2) : nsigma.toFixed() ) + " σ " + (isneg ? "below" : "above") + " background.");
    ypos += 15;

  } else if (!sigmaCount.empty()) {
      sigmaCount.remove();
  }

  /* Output all the corresponding asterick text with each spectrum (if scale factor != 1) */
  specialScaleSpectras.forEach(function(string, i) {
    if (string == null || !string.length)
      return;
    var stringnode = d3.select("#asterickText" + i);

    if (stringnode.empty())
      stringnode = self.vis.append("text")
        .attr("id", "asterickText"+i)
        .attr("class", "countGammasText asterickText")
        .text(string);
    stringnode.attr("x", Number(countGammasBox.attr("x")) + (Number(countGammasBox.attr("width"))/2) + rightPadding/3)
      .attr("y", ypos);
    ypos += 15;
  });

  /* Hide all the count gamma text when the mouse box is empty */
  if (Number(countGammasBox.attr("width")) == 0)
    d3.selectAll(".countGammasText").attr("fill-opacity", 0);
  else
    d3.selectAll(".countGammasText").attr("fill-opacity", 1);
}


SpectrumChartD3.prototype.handleMouseUpCountGammas = function() {
  var self = this;

  var countGammasBox = d3.select("#countGammasBox"),
      countGammasText = d3.select("#countGammasText");

  var countGammasRange;

  try {
    countGammasRange = [ 
      Math.min(self.xScale.invert(Number(countGammasBox.attr("x"))), self.xScale.invert(Number(countGammasBox.attr("x")) + Number(countGammasBox.attr("width")))), 
      Math.max(self.xScale.invert(Number(countGammasBox.attr("x"))), self.xScale.invert(Number(countGammasBox.attr("x")) + Number(countGammasBox.attr("width")))) 
      ];

    if (self.lastMouseMovePos[0] < self.countGammasMouse[0]) {
      console.log("Emit REMOVE GAMMA COUNT SIGNAL FROM ", countGammasRange[0], "keV to ", countGammasRange[1], " keV" );
    } else {
      console.log("Emit COUNT GAMMAS SIGNAL FROM ", countGammasRange[0], "keV to ", countGammasRange[1], " keV" );
    }

    self.WtEmit(self.chart.id, {name: 'shiftaltkeydragged'}, countGammasRange[0], countGammasRange[1]);
    
  } catch (TypeError) { /* For some reason, a type error is (seldom) returned when trying to access "x" attribute of countGammasBox, doesn't affect overall functionality though */
    return;
  }

  self.handleCancelMouseCountGammas();
}

SpectrumChartD3.prototype.handleCancelMouseCountGammas = function() {
  var self = this;

  var countGammasBox = d3.select("#countGammasBox"),
      countGammasText = d3.select("#countGammasText");

  /* Delete the count gammas box since we are not counting gammas anymore */
  countGammasBox.remove();

  /* Delete the count gamma texts since we are not counting gammas anymore */
  self.vis.selectAll(".countGammasText").remove()

  /* We are not erasing peaks anymore */
  self.isCountingGammas = false;
}

SpectrumChartD3.prototype.handleTouchMoveCountGammas = function() {
  var self = this;

  /* Cancel delete peaks mode */
  self.handleCancelTouchDeletePeak();

  /* Cancel the create peaks mode */
  self.handleCancelTouchPeakFit();

  /* Cancel the zoom-in y mode */
  self.handleTouchCancelZoomInY();


  var t = d3.touches(self.vis[0][0]);

  if (t.length !== 2 || !self.countGammasStartTouches || !self.rawData || !self.rawData.spectra ) {
    self.handleCancelTouchCountGammas();
    return;
  }

 
  
  function needsDecimal(num) {
    return num % 1 != 0;
  }

  var leftStartTouch = self.countGammasStartTouches[0][0] < self.countGammasStartTouches[1][0] ? self.countGammasStartTouches[0] : self.countGammasStartTouches[1],
      rightStartTouch = leftStartTouch === self.countGammasStartTouches[0] ? self.countGammasStartTouches[1] : self.countGammasStartTouches[0];

  var leftTouch = t[0][0] < t[1][0] ? t[0] : t[1],
      rightTouch = leftTouch === t[0] ? t[1] : t[0];

  var countGammasBox = d3.select("#countGammasBox"),
      countGammasText = d3.select("#countGammasText"),
      countGammaRangeText = d3.select("#countGammaRangeText"),
      foregroundCountsText = d3.select("#foregroundCountsText"),
      backgroundCountsText = d3.select("#backgroundCountsText"),
      secondaryCountsText = d3.select("#secondaryCountsText")
      foregroundAsterickText = d3.select("#foregroundAsterickText"),
      backgroundAsterickText = d3.select("#backgroundAsterickText"),
      secondaryAsterickText = d3.select("#secondaryAsterickText"),
      sigmaCount = d3.select("#sigmaCount");

  var countGammasRange = [ 
      self.xScale.invert(leftStartTouch[0]), 
      Math.min(self.xScale.invert(rightTouch[0]), self.xScale.domain()[1])
  ];
  
  let startx = leftStartTouch[0];
  let nowx = rightTouch[0];

  /* Create the yellow box and text associated with it */
  if (countGammasBox.empty()) { 
    countGammasBox = self.vis.append("rect")
      .attr("id", "countGammasBox")
      .attr("width", Math.min( Math.abs( startx - nowx ) , Math.abs( self.xScale.range()[1] - startx ) ))
      .attr("height", self.size.height)
      .attr("y", 0);

  } else {  /* Adjust the width of the erase peaks box */
    countGammasBox.attr("width", Math.min( Math.abs( startx - nowx ) , Math.abs( self.xScale.range()[1] - startx ) ));
  }
  if (countGammasText.empty()) {
    countGammasText = self.vis.append("text")
      .attr("id", "countGammasText")
      .attr("class", "countGammasText")
      .attr("y", Number(countGammasBox.attr("height"))/2)
      .text("Gamma Counts");
  }
  var ypos = Number(countGammasBox.attr("height"))/2 + 15;   /* signifies the y-position of the text displayed */

  /* Mouse position to the left of initial starting point of count gammas box */
  if (nowx  <= startx) {
    countGammasBox.attr("class", "deletePeaksBox")
      .attr("x", nowx);
    countGammasText.text("Will remove gamma count range");

    /* Move the count gammas text in the middle of the count gammas box */
    countGammasText.attr("x", Number(countGammasBox.attr("x")) + (Number(countGammasBox.attr("width"))/2) - 30 /*Number(countGammasText[0][0].clientWidth)/2*/ );

    /* Remove the counts text (we will not be counting gammas) */
    d3.selectAll('.asterickText').remove();
    self.rawData.spectra.forEach(function(spectrum, i) {
      d3.select('#Spectrum-' + spectrum.id + 'CountsText').remove();
      d3.select('#Spectrum-' + spectrum.id + 'AsterickText').remove();
      d3.select("#asterickText"+i).remove();
    });
    countGammaRangeText.remove();
    sigmaCount.remove();

    return;

  } else {
    countGammasBox.attr("class", "countGammasBoxForward")
      .attr("x", nowx < startx ? nowx : startx);
    countGammasText.text("Gamma Counts");

    if (countGammaRangeText.empty())
      countGammaRangeText = self.vis.append("text")
        .attr("id", "countGammaRangeText")
        .attr("class", "countGammasText")
        .attr("y", ypos);


    countGammaRangeText.text((needsDecimal(countGammasRange[0]) ? countGammasRange[0].toFixed(1) : countGammasRange[0].toFixed()) + 
                              " to " + 
                              (needsDecimal(countGammasRange[1]) ? countGammasRange[1].toFixed(1) : countGammasRange[1].toFixed()) + " keV");
    countGammaRangeText.attr("x", Number(countGammasBox.attr("x")) + (Number(countGammasBox.attr("width"))/2) - 30 /*Number(countGammaRangeText[0][0].clientWidth)/2*/);
  }
  ypos += 15;

  /* Move the count gammas text in the middle of the count gammas box */
  countGammasText.attr("x", Number(countGammasBox.attr("x")) + (Number(countGammasBox.attr("width"))/2) - 30 /*Number(countGammasText[0][0].clientWidth)/2*/ );

  /* Display the count gammas text for all the spectrum */
  var nforeground, nbackground, backSF;
  var nsigma = 0, isneg;
  var asterickText = "";
  var rightPadding = 50;
  var specialScaleSpectras = [];
  self.rawData.spectra.forEach(function(spectrum, i) {   /* TODO: May need to change processing of */
    if (!spectrum)
      return;

    /* Get information from the spectrum */
    var spectrumSelector = 'Spectrum-' + spectrum.id;
    var spectrumCountsText = d3.select("#" + spectrumSelector + "CountsText");
    var spectrumScaleFactor = spectrum.yScaleFactor;
    var nspectrum = self.gammaIntegral(spectrum, countGammasRange[0], countGammasRange[1]);
    var spectrumGammaCount = Number((spectrumScaleFactor * nspectrum).toFixed(2));
    var countsText;

    /* Save information for the foreground and background (for sigma comparison) */
    if (spectrum.type === self.spectrumTypes.FOREGROUND)
      nforeground = nspectrum;
    else if (spectrum.type === self.spectrumTypes.BACKGROUND) {
      nbackground = nspectrum;
      backSF = spectrumScaleFactor;
    }

    /* Get the text to be displayed from the spectrum information */
    if (spectrumScaleFactor != null && spectrumScaleFactor !== -1)
      countsText = spectrum.title + ": " + (needsDecimal(spectrumGammaCount) ? spectrumGammaCount.toFixed(2) : spectrumGammaCount.toFixed());
    if (spectrumScaleFactor != 1) {
      asterickText += "*";
      if (countsText)
        countsText += asterickText;
      specialScaleSpectras.push(asterickText + "scaled by " + 
        (needsDecimal(spectrumScaleFactor) ? spectrumScaleFactor.toFixed(3) : spectrumScaleFactor.toFixed()) + " from actual");
    }

    /* Output the count gammas information to the chart */
    if (countsText) {
      if (spectrumCountsText.empty())
        spectrumCountsText = self.vis.append("text")
          .attr("id", spectrumSelector + "CountsText")
          .attr("class", "countGammasText")
          .attr("y", ypos);
      spectrumCountsText.text(countsText); 
      spectrumCountsText.attr("x", Number(countGammasText.attr("x")) - rightPadding );
      ypos += 15;

    } else {
      spectrumCountsText.remove();
    }
  });

  /* Get proper information for foreground-background sigma comparison */
  if (nforeground && nbackground && backSF) {
    const backSigma = backSF * Math.sqrt(nbackground);
    const sigma = Math.sqrt(backSigma*backSigma + nforeground); //uncert_fore=sqrt(nforeground) since foregoround SF is always 1.0
    nsigma = sigma == 0 ? 0 : (Number((Math.abs(nforeground - nbackground*backSF) / sigma).toFixed(3)));
    isneg = ((nbackground*backSF) > nforeground);
  }

  /* Output foreground-background sigma information if it is available */
  if (nsigma > 0) {
    if (sigmaCount.empty())
      sigmaCount = self.vis.append("text")
        .attr("id", "sigmaCount")
        .attr("class", "countGammasText")
        .attr("y", ypos);

    sigmaCount.attr("x", Number(countGammasText.attr("x")) - rightPadding + 10)
      .text("Foreground is " + (needsDecimal(nsigma) ? nsigma.toFixed(2) : nsigma.toFixed() ) + " σ " + (isneg ? "below" : "above") + " background.");
    ypos += 15;

  } else if (!sigmaCount.empty()) {
      sigmaCount.remove();
  }

  /* Output all the corresponding asterick text with each spectrum (if scale factor != 1) */
  specialScaleSpectras.forEach(function(string, i) {
    if (string == null || !string.length)
      return;
    var stringnode = d3.select("#asterickText" + i);

    if (stringnode.empty())
      stringnode = self.vis.append("text")
        .attr("id", "asterickText"+i)
        .attr("class", "countGammasText asterickText")
        .text(string);
    stringnode.attr("x", Number(countGammasBox.attr("x")) + (Number(countGammasBox.attr("width"))/2) + rightPadding/3)
      .attr("y", ypos);
    ypos += 15;
  });

  /* Hide all the count gamma text when the mouse box is empty */
  if (Number(countGammasBox.attr("width")) == 0)
    d3.selectAll(".countGammasText").attr("fill-opacity", 0);
  else
    d3.selectAll(".countGammasText").attr("fill-opacity", 1);
}

SpectrumChartD3.prototype.handleTouchEndCountGammas = function() {
  var self = this;

  var countGammasBox = d3.select("#countGammasBox"),
      countGammasText = d3.select("#countGammasText");

  var countGammasRange;

  try {
    countGammasRange = [ 
      Math.min(self.xScale.invert(Number(countGammasBox.attr("x"))), self.xScale.invert(Number(countGammasBox.attr("x")) + Number(countGammasBox.attr("width")))), 
      Math.max(self.xScale.invert(Number(countGammasBox.attr("x"))), self.xScale.invert(Number(countGammasBox.attr("x")) + Number(countGammasBox.attr("width")))) 
      ];

    console.log("Emit COUNT GAMMAS SIGNAL FROM ", countGammasRange[0], "keV to ", countGammasRange[1], " keV" );
    self.WtEmit(self.chart.id, {name: 'shiftaltkeydragged'}, countGammasRange[0], countGammasRange[1]);

  } catch (TypeError) { /* For some reason, a type error is (seldom) returned when trying to access "x" attribute of countGammasBox, doesn't affect overall functionality though */
    return;
  }

  self.handleCancelTouchCountGammas();
}

SpectrumChartD3.prototype.handleCancelTouchCountGammas = function() {
  var self = this;

  var countGammasBox = d3.select("#countGammasBox"),
      countGammasText = d3.select("#countGammasText"),
      foregroundCountsText = d3.select("#foregroundCountsText"),
      backgroundCountsText = d3.select("#backgroundCountsText"),
      secondaryCountsText = d3.select("#secondaryCountsText");

  /* Delete the count gammas box since we are not counting gammas anymore */
  countGammasBox.remove();

  /* Delete the count gamma texts since we are not counting gammas anymore */
  d3.selectAll(".countGammasText").forEach(function (texts) {
    texts.forEach(function(text) {
      text.remove();
    })
  });
}


/**
 * -------------- Peak Info and Display Functions --------------
 */
SpectrumChartD3.prototype.handleMouseOverPeak = function( peakElem ) {
  //console.log( 'handleMouseOverPeak' );
  this.highlightPeak(peakElem,true);
  // self.displayPeakInfo(info, d3.event.x);
}

SpectrumChartD3.prototype.handleMouseOutPeak = function(peakElem, highlightedPeak, paths) {
  var self = this;

  var event = d3.event;

  /* Returns true if a node is a descendant (or is) of a parent node. */
  function isElementDescendantOf(parent, node) {
    while (node != null) {
      if (node == parent) return true;
      node = node.parentNode;
    }
    return false;
  }
  
  if (self.peakInfo && isElementDescendantOf(self.peakInfo.node(), event.toElement)) {
    return self.handleMouseMovePeak()();
  }

  self.unhighlightPeak(highlightedPeak);
}

SpectrumChartD3.prototype.handleMouseMovePeak = function() {
  var self = this;

  return function() {
    const event = d3.event;

    if (self.peakInfo) {
      const x = event.x;
      const box = self.peakInfoBox;
      const translate = Number(self.peakInfo.attr("transform")
        .replace("translate(", "")
        .replace(")","")
        .split(',')[0]);

      const shouldMovePeakInfoLeft = x >= box.x && x <= box.x + box.width;

      self.peakInfo.attr("transform","translate(" 
        + (shouldMovePeakInfoLeft ? (self.padding.leftComputed + 115) : self.size.width) 
        + "," + (self.size.height - 40) + ")");
    }
  }
}

SpectrumChartD3.prototype.getPeakInfoObject = function(roi, energy, spectrumIndex) {
  var self = this;

  // No ROI given, so skip
  if (!roi) 
    return null;

  let peak;
  let minDistance = Infinity;

  roi.peaks.forEach(function(roiPeak) {
    const distance = Math.abs(energy - roiPeak.Centroid[0]);

    if (distance < minDistance) {
      minDistance = distance;
      peak = roiPeak;
    }
  });

  // No peak found, so skip
  if (!peak) 
    return null;

  const coeffs = roi.coeffs;
  const referenceEnergy = roi.referenceEnergy;
  const lowerEnergy = roi.lowerEnergy;
  const upperEnergy = roi.upperEnergy;

  const mean = peak.Centroid[0].toFixed(2);
  let fwhm = 2.35482 * peak.Width[0];
  fwhm = fwhm.toFixed( ((fwhm < 10) ? ((fwhm < 1) ? 4 : 3) : 2) );
  const fwhmPerc = (235.482 * peak.Width[0] / peak.Centroid[0]).toFixed(2);
  const chi2 = peak.Chi2[0].toFixed(2);
  const area = peak.Amplitude[0].toFixed(1);
  const areaUncert = peak.Amplitude[1].toFixed(1);

  let nuc = null;
  if( peak.nuclide && peak.nuclide.name ){
    //nuclide: {name: "Eu152", decayParent: "Eu152", decayChild: "Sm152", energy: 1408.01}
    nuc = peak.nuclide.name + " (";
    if( peak.nuclide.decayParent !== peak.nuclide.name )
      nuc = nuc + peak.nuclide.decayParent + ", ";
    if( peak.nuclide.energy )
      nuc = nuc + peak.nuclide.energy.toFixed(2) + " keV";
    if( peak.nuclide.type )
      nuc = nuc + " " + peak.nuclide.type;
    nuc = nuc + ")";
  }
  

  const contArea = self.offset_integral(roi,lowerEnergy, upperEnergy).toFixed(1);
  
  const info = {
    mean: mean, 
    fwhm: fwhm, 
    fwhmPerc: fwhmPerc, 
    chi2: chi2, 
    area: area, 
    areaUncert: areaUncert, 
    contArea: contArea, 
    spectrumIndex: spectrumIndex,
    nuclide: nuc
  };
  return info;
}

SpectrumChartD3.prototype.updatePeakInfo = function() {
  var self = this;

  if (!self.rawData || !self.rawData.spectra || !self.rawData.spectra.length)
    return;

  const x = d3.mouse(self.vis.node())[0];
  const energy = self.xScale.invert(x);
  let resultROI;
  let spectrumIndex;

  // Find a peak that our mouse energy point is overlapping with
  self.rawData.spectra.forEach(function(spectrum, i) {
    if (resultROI) // we found a peak already, skip the rest
      return;
    if (!self.options.drawPeaksFor[spectrum.type])
      return;

    spectrum.peaks.forEach(function(peak, j) {
      if (!resultROI && peak.lowerEnergy <= energy && energy <= peak.upperEnergy) {  // we haven't found a peak yet
        resultROI = peak;
        spectrumIndex = i;
      }
    });
  });
  
  // No peak found, so hide the info box
  if (!resultROI) {
    self.hidePeakInfo();
    return;
  } 
  
  const info = self.getPeakInfoObject(resultROI, energy, spectrumIndex);
  self.displayPeakInfo(info);
}

SpectrumChartD3.prototype.displayPeakInfo = function(info) {
  var self = this;

  function createPeakInfoText(text, label, value, special) {
    let span = text.append("tspan")
      .attr('class', "peakInfoLabel")
      .attr('x', "-13.5em")
      .attr('dy', "-1em")
      .text(label + ': ');
    span.append("tspan")
      .style('font-weight', "normal")
      .text( value );
  }

  const areMultipleSpectrumPeaksShown = self.areMultipleSpectrumPeaksShown();
  let x = d3.event.clientX;

  self.hidePeakInfo();

  let boxy = areMultipleSpectrumPeaksShown ? -7.1 : -6.1;
  let boxheight = areMultipleSpectrumPeaksShown ? 6.5 : 5.5;
  if( info.nuclide ){
    boxy -= 1;
    boxheight += 1;
  }
  
  self.peakInfo = self.vis.append("g")
    .attr("class", "peakInfo")
    .attr("transform","translate(" + self.size.width + "," + (self.size.height - 40) + ")");

  var rect = self.peakInfo.append('rect')
    .attr("class", "peakInfoBox")
    .attr('height', boxheight + "em")
    .attr('x', "-14em")
    .attr('y', boxy + "em")
    .attr('rx', "5px")
    .attr('ry', "5px");

  var text = self.peakInfo.append("g")
    .append("text")
    .attr("dy", "-2em");
  
  if( info.nuclide ){
    text.append("tspan")
        .style('font-weight', "normal")
        .attr('x', "-13.5em")
        .attr('dy', "-1em")
        .text( info.nuclide );
  }
    
  createPeakInfoText(text, "cont. area", info.contArea);
  createPeakInfoText(text, "peak area", info.area + String.fromCharCode(0x00B1) + info.areaUncert);
  createPeakInfoText(text, String.fromCharCode(0x03C7) + "2/dof", info.chi2);
  createPeakInfoText(text, "FWHM", info.fwhm + " keV (" + info.fwhmPerc + "%)");
  createPeakInfoText(text, "mean", info.mean + " keV");
  
  if (areMultipleSpectrumPeaksShown)
    createPeakInfoText(text, "Spectrum", self.rawData.spectra[info.spectrumIndex].title);
    
  const width = text.node().getBoundingClientRect().width + 10; // + 10 for padding right
  rect.attr('width', width);

  self.peakInfoBox = self.peakInfo.node().getBoundingClientRect();

  if (x >= (self.peakInfoBox.x ? self.peakInfoBox.x : self.peakInfoBox.left))
    self.peakInfo.attr("transform","translate(" + (self.padding.leftComputed + 115) + "," + (self.size.height - 40) + ")");
}

SpectrumChartD3.prototype.hidePeakInfo = function() {
  var self = this;

  if (!self.peakInfo) return;

  self.peakInfo.remove();
  self.peakInfo = null;
}

/**
 @param peakElem The HTML peak path that
 */
SpectrumChartD3.prototype.highlightPeak = function( peakElem, highlightLabelTo ) {
  var self = this;

  if( self.zooming_plot || !peakElem || self.leftMouseDown || self.rightClickDown )
    return;

  if( self.highlightedPeak )
    self.unhighlightPeak(null);
    
  var peak = d3.select(peakElem);
  if( Array.isArray(peak[0][0]) )
    peak = peakElem;

  if( peak )
    peak.attr("stroke-width",2);
  
  self.highlightedPeak = peakElem;
  
  if( !highlightLabelTo )
    return;
  
  //Dont waste time selecting for label elements if there is no possibility of having them - not sure this saves anything...
  if( !this.options.showUserLabels && !this.options.showPeakLabels && !this.options.showNuclideNames )
    return;
  
  self.peakVis.select('text[data-peak-energy="' + peakElem.dataset.energy + '"].peaklabel').each( function(){
    self.highlightLabel(this,true);
  });
}//SpectrumChartD3.prototype.highlightPeak = ...


SpectrumChartD3.prototype.unhighlightPeak = function(highlightedPeak) {
  var self = this;

  if( !highlightedPeak )
    highlightedPeak = self.highlightedPeak;
  
  if( !highlightedPeak )
    return;
    
  if( !Array.isArray(highlightedPeak) )
    highlightedPeak = d3.select(highlightedPeak);
  
  highlightedPeak.attr("stroke-width",1);
  self.highlightedPeak = null;
  
  if( self.highlightedLabel )
    self.unHighlightLabel(false);
}


/* Highlight a peaks label.
 
 This means:
 - Label becomes bold
 - Label's z-index goes to very top (so that the whole text is shown)
 - A line is drawn from the label to its corresponding peak
 
 @param labelEl The HTML the <text> element of the label to highlight.
 @param isFromPeakBeingHighlighted Boolean telling whether we are highlighting the
        label because the peak is being moused-over, or the label is being moused-over.
        If label is being moused over, we will also highlight the peak, and make a
        line that goes from the label to middle of peak.  If its the peak being
        moused over, we wont highlight the peak (because that is already being done),
        and we will draw a line to either the top or bottom of peak (whichever is closer)
 */
SpectrumChartD3.prototype.highlightLabel = function( labelEl, isFromPeakBeingHighlighted ) {
  let self = this;
  
  //console.log( 'Highlighting label ' + labelEl.dataset.peakXPx + ' keV' );
  
  if( self.highlightedLabel === labelEl )
    return;
    
  if( self.highlightedLabel )
    self.unHighlightLabel(true);
  
  if( self.dragging_plot )
    return;
  
  /* Bold the label text and add a line (arrow) that points to the peak when moused over text. */
  self.highlightedLabel = labelEl;
  
  let thislabel = d3.select(labelEl);
  thislabel.attr('class', 'peakLabelBold');
  
  const labelbbox = thislabel.node().getBBox();
  const labelTop = labelbbox.y,
  labelBottom = labelbbox.y + labelbbox.height;
  
  /*
   //I think we have to make the rect right before the <text>....
   // Should put <rect> and <text> within a <g> (and use a transform to place
   // everything), if we want to draw a border around the text.
  self.peakVis.append("rect")
  .attr("width", labelbbox.width)
  .attr("height", labelbbox.height)
  .attr("x", labelbbox.x)
  .attr("y", labelbbox.y)
  .attr("class", 'peakLabelBorder' );
  */
  
  const x1 = labelbbox.x + 0.5*labelbbox.width;
  const x2 = labelEl.dataset.peakXPx;
  const y1 = ((labelTop > labelEl.dataset.peakLowerYPx) ? labelTop : labelBottom);
  let y2 = 0.5*(parseFloat(labelEl.dataset.peakLowerYPx) + parseFloat(labelEl.dataset.peakUpperYPx));
  if( isFromPeakBeingHighlighted )
    y2 = (labelbbox.y > labelEl.dataset.peakLowerYPx) ? labelEl.dataset.peakLowerYPx : labelEl.dataset.peakUpperYPx;
  
  //console.log( 'x1=' + x1 + ', x2=' + x2 + ', y1=' + y1 + ', y2=' + y2 );
  
  const tickElement = document.querySelector('.tick');
  const tickStyle = tickElement ? getComputedStyle(tickElement) : null;
  let axiscolor = tickStyle && tickStyle.stroke ? tickStyle.stroke : 'black';
  
  //Only draw line between label and peak if it will be at least 10 pixels.
  if( Math.sqrt( Math.pow(x1-x2,2) + Math.pow(y1-y2,2) ) > 10 )
    self.peakLabelLine = self.peakVis.append('line')
        .attr('class', 'peaklabelline')
        .attr('x1', x1)
        .attr('y1', y1)
        .attr('x2', x2)
        .attr('y2', y2)
        .attr('stroke', axiscolor)
        .attr("marker-end", "url(#triangle)");
  
  if( isFromPeakBeingHighlighted )
    return;
  
  //Highlight peak cooresponding to this label
  self.peakVis.select('path[data-energy="' + labelEl.dataset.peakEnergy + '"].peakFill').each( function(){
    self.highlightPeak(this,false);
  });
}//function highlightLabel()

/** Un-highlight the currently highlighted peak (pointed to by self.highlightedLabel)
 
 @param unHighlightPeakTo Boolean describing if the peak cooresponding to this
        label should also be un-highlighted.
 */
SpectrumChartD3.prototype.unHighlightLabel = function( unHighlightPeakTo ) {
  let self = this;
  
  if( !self.highlightedLabel )
    return;
  
  if( unHighlightPeakTo ){
    const peakEnergy = self.highlightedLabel.dataset.peakEnergy;
    self.peakVis.select('path[data-energy="' + peakEnergy + '"].peakFill').each( function(){
      self.unhighlightPeak(this);
    });
  }
  
  /* Return label back to original style on mouse-out. */
  d3.select(self.highlightedLabel).attr('class', 'peaklabel');
  
  /* delete the pointer line from the label to the peak */
  if( self.peakLabelLine ) {
    self.peakLabelLine.remove();
    self.peakLabelLine = null;
  }
  
  self.highlightedLabel = null;
}//function unHighlightLabel(...)





/**
 * -------------- Background Subtract Functions --------------
 */
SpectrumChartD3.prototype.setBackgroundSubtract = function( subtract ) {
  var self = this;

/*
  var checkbox = document.getElementById('background-subtract-option');

  if (!self.rawData || !self.rawData.spectra || !self.rawData.spectra.length) {
    alert('No data specified!');
    if (checkbox) checkbox.checked = false;
    return;
  }

  if (self.rawData.spectra.filter(function(spectrum) { return spectrum.type == self.spectrumTypes.BACKGROUND }).length !== 1) {
    alert('Need only one background spectrum for background subtract!');
    if (checkbox) checkbox.checked = false;
    return;
  }
*/
  
  self.options.backgroundSubtract = Boolean(subtract);
  self.redraw()();
}

SpectrumChartD3.prototype.rebinForBackgroundSubtract = function() {
  var self = this;

  // Don't do anything if no data exists
  if (!self.rawData || !self.rawData.spectra || !self.rawData.spectra.length)
    return;

  // Don't do anything else if option is not toggled
  if (!self.options.backgroundSubtract)
    return;
  
  var bisector = d3.bisector(function(point) { return point.x });

  self.rawData.spectra.forEach(function(spectrum) {
    // We don't need to generate the points for background subtract for a background spectrum
    if (spectrum.type === self.spectrumTypes.BACKGROUND) return;

    // Initialize background subtract points for this spectrum to be empty
    spectrum.bgsubtractpoints = [];

    const background = self.getSpectrumByID(spectrum.backgroundID);

    // Don't add any points if there is no associated background with this spectrum
    if (!background) return;

    // Get points for background subtract for this spectrum by getting the nearest background point and subtracting y-values
    spectrum.bgsubtractpoints = spectrum.points.map(function(point) {
      const x = point.x;
      const y = point.y;
      const bpoint = background.points[bisector.left(background.points, x)];
      if (!bpoint) return { x: x, y: 0 };
      return { x: x, y: Math.max(0, y - bpoint.y) };
    });
  });
}



/**
 * -------------- Helper Functions --------------
 */
/**
 * Returns true if the browser has touch capabilities, false otherwise.
 * Thanks to: https://stackoverflow.com/questions/4817029/whats-the-best-way-to-detect-a-touch-screen-device-using-javascript
 */
SpectrumChartD3.prototype.isTouchDevice = function() {
  return 'ontouchstart' in window        // works on most browsers 
      || navigator.maxTouchPoints;       // works on IE10/11 and Surface
}

SpectrumChartD3.prototype.isWindows = function() {
  return navigator.appVersion.indexOf("Win") != -1;
}

/**
 * Returns true if multiple spectra are showing peaks.
 */
SpectrumChartD3.prototype.areMultipleSpectrumPeaksShown = function() {
  var self = this;

  if (!self.rawData || !self.rawData.spectra || !self.rawData.spectra.length)
    return false;

  let numberOfSpectraPeaks = 0;

  self.rawData.spectra.forEach(function(spectrum) {
    if (spectrum.peaks && spectrum.peaks.length && self.options.drawPeaksFor[spectrum.type])
      numberOfSpectraPeaks++;
  });

  return numberOfSpectraPeaks > 1;
}

/**
 * Returns the spectrum with a given ID. If no specturm is found, then null is returned.
 * Assumes valid data, so if there are multiple spectra with same ID, then the first one is returned.
 */
SpectrumChartD3.prototype.getSpectrumByID = function(id) {
  var self = this;

  if (!self.rawData || !self.rawData.spectra || !self.rawData.spectra.length)
    return;

  for (let i = 0; i < self.rawData.spectra.length; i++) {
    if (self.rawData.spectra[i].id === id)
      return self.rawData.spectra[i];
  }

  return null;
}

/**
 * Returns a list of all spectra title names.
 */
SpectrumChartD3.prototype.getSpectrumTitles = function() {
  var self = this;

  if (!self.rawData || !self.rawData.spectra || !self.rawData.spectra.length)
    return;

  var result = [];
  self.rawData.spectra.forEach(function(spectrum, i) {
    if (spectrum.title)
      result.push(spectrum.title);
    else  /* Spectrum title doesn't exist, so use default format of "Spectrum #" */
      result.push("Spectrum " + (i + 1));
  });
  return result;
}


/**
 * Returns the number of counts for a specific energy value.
 */
SpectrumChartD3.prototype.getCountsForEnergy = function(spectrum, energy) {
  var self = this;

  if (!self.rawData || !self.rawData.spectra || !spectrum || !spectrum.x)
    return -1;

  var channel, lowerchanval, counts = null;
  var spectrumIndex = self.rawData.spectra.indexOf(spectrum);

  if (spectrumIndex < 0)
    return -1;

  channel = d3.bisector(function(d){return d;}).right(spectrum.x, energy);

  if( spectrum.points && spectrum.points.length ){
    lowerchanval = d3.bisector(function(d){return d.x;}).left(spectrum.points,energy,1) - 1;
    counts = spectrum.points[lowerchanval].y;
  }
  return counts;
}



/* Returns the data y-range for the currently viewed x-range. */
SpectrumChartD3.prototype.getYAxisDataDomain = function(){
  var self = this;
  
  if( !self.rawData || !self.rawData.spectra || !self.rawData.spectra.length )
    return [0, 3000];
  
  var key = self.options.backgroundSubtract ? 'bgsubtractpoints' : 'points';  // Figure out which set of points to use
  var y0, y1;
  var minx = self.xScale.domain()[0], maxx = self.xScale.domain()[1];
  var foreground = self.rawData.spectra[0];
  var firstData = self.displayed_start(foreground);
  var lastData = self.displayed_end(foreground);
  
  if( firstData >= 0 ){
    y0 = y1 = foreground[key][firstData].y;
    
    self.rawData.spectra.forEach(function(spectrum) {
      // Don't consider background spectrum if we're viewing the Background Subtract
      if (self.options.backgroundSubtract && spectrum.type === self.spectrumTypes.BACKGROUND) return;
      firstData = self.displayed_start(spectrum);
      lastData = self.displayed_end(spectrum);
      
      for (var i = firstData; i < lastData; i++) {
        if (spectrum[key][i]) {
          y0 = Math.min( y0, spectrum[key][i].y );
          y1 = Math.max( y1, spectrum[key][i].y );
        }
      }
    });
  }else {
    y0 = 0;
    y1 = 3000;
  }
  
  if( y0 > y1 ) { y1 = [y0, y0 = y1][0]; }
  if( y0 == y1 ){ y0 -=1; y1 += 1; }

  return [y0, y1];
}

/**
 * Returns the Y-axis domain based on the current set of zoomed-in data, with user preffered padding amounts accounted for.
 */
SpectrumChartD3.prototype.getYAxisDomain = function(){
  var self = this;

  if (!self.rawData || !self.rawData.spectra || !self.rawData.spectra.length)
    return [3000,0];
    
  let yrange, y0, y1;
  yrange = self.getYAxisDataDomain();
  y0 = yrange[0];
  y1 = yrange[1];
  
  
  if( self.options.yscale == "log" ) {
    /*Specify the (approx) fraction of the chart that the scale should extend */
    /*  past where the data where hit. */
    var yfractop = self.options.logYFracTop, yfracbottom = self.options.logYFracBottom;

    var y0Intitial = ((y0<=0.0) ? 0.1 : y0);
    var y1Intitial = ((y1<=0.0) ? 1.0 : y1);
    y1Intitial = ((y1Intitial<=y0Intitial) ? 1.1*y0Intitial : y1Intitial);

    var logY0 = Math.log10(y0Intitial);
    var logY1 = Math.log10(y1Intitial);

    var logLowerY = ((y0<=0.0) ? -1.0 : (logY0 - yfracbottom*(logY1-logY0)));
    var logUpperY = logY1 + yfractop*(logY1-logY0);

    var ylower = Math.pow( 10.0, logLowerY );
    var yupper = Math.pow( 10.0, logUpperY );

    y0 = ((y0<=0.0) ? 0.1 : ylower);
    y1 = ((y1<=0.0) ? 1.0 : yupper);
  } else if( self.options.yscale == "lin" )  {
    y0 = ((y0 <= 0.0) ? (1+self.options.linYFracBottom)*y0 : (1-self.options.linYFracBottom)*y0);
    y1 = (1 + self.options.linYFracTop)*y1;
  } else if( self.options.yscale == "sqrt" ) {
    y0 = ((y0 <= 0.0) ? 0.0 : (1-self.options.sqrtYFracBottom)*y0);
    y1 = (1+self.options.sqrtYFracTop)*y1;
  }

  return [y1,y0];
}

/**
 * Returns a random color based on hexadecimal value.
 */
SpectrumChartD3.prototype.getRandomColor = function() {
  let hex = '#';
  const letters = '0123456789ABCDEF';

  for (let i = 0; i < 6; i++)
    hex += letters.charAt(Math.floor(Math.random() * 15));
  
  return hex;
}
