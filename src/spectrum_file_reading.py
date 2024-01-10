from .table_def import *
from .rase_functions import ConvertDurationToSeconds, get_ET_from_file, uncompressCountedZeroes, getSeconds
import ntpath, sys
# see base_from_dynamic.py for ideas on how to do this


class BaseSpectraFormatException(Exception):
    pass

all_spec = { 'measurements' : ('./RadMeasurement', './Measurement'),
                    'channeldata': ('./Spectrum/ChannelData'),
                  'realtime': ('./RealTimeDuration', './Spectrum/RealTime'),
                  'livetime': ('./Spectrum/LiveTimeDuration', './Spectrum/LiveTime'),
                  'calibration': ('./EnergyCalibration/CoefficientValues',
                                  './Measurement/Spectrum/Calibration/Equation/Coefficients'),
                  'RASE_sensitivity': './Spectrum/RASE_Sensitivity',
                  'FLUX_sensitivity': './Spectrum/FLUX_Sensitivity',
                  'classcode': './MeasurementClassCode'
                }



def yield_spectra(n42root, spec):
    """
    Read base spectra from .n42 files into memory
    @param n42root:
    @param spec:
    @return:
    """
    calibration_el = requiredElement(spec['calibration'], n42root, 'calibration measurement')
    ecal = [float(value) for value in calibration_el.text.split()]

    measurement_els = []
    for measpath in spec['measurements']:
        measurement_els += n42root.xpath(measpath)
    for measurement in measurement_els:
        channeldata_el = requiredElement(spec['channeldata'], measurement, 'spectrum counts data')
        countsChar = channeldata_el.text.strip("'").strip().split()
        if len(countsChar) < 2:
            countsChar = channeldata_el.text.strip("'").strip().split(',')
        counts_num = [float(f) for f in uncompressCountedZeroes(channeldata_el,
                                            [float(c) for c in countsChar]).strip().split(',')]
        realtime_el = requiredElement(spec['realtime'], measurement, 'realtime measurement')
        realtime = ConvertDurationToSeconds(realtime_el.text)
        livetime_el = requiredElement(spec['livetime'], measurement, 'livetime measurement')
        livetime = ConvertDurationToSeconds(livetime_el.text)
        try:
            classcode_el = requiredElement(spec['classcode'], measurement, 'Measurement Class Code')
            classcode = classcode_el.text
            if classcode == 'Foreground':
                RASEsensElement = requiredSensitivity((spec['RASE_sensitivity'], spec['FLUX_sensitivity']), measurement)
                if RASEsensElement is not None:
                    if RASEsensElement[0] is None:
                        rase_sensitivity = 'NaN'
                    else:
                        rase_sensitivity = float(RASEsensElement[0].text.strip())
                    if RASEsensElement[1] is None:
                        flux_sensitivity = 'NaN'
                    else:
                        flux_sensitivity = float(RASEsensElement[1].text.strip())
                spectrum = BaseSpectrum(counts=counts_num,
                                        realtime=realtime,
                                        livetime=livetime,
                                        ecal=ecal,
                                        rase_sensitivity=rase_sensitivity,
                                        flux_sensitivity=flux_sensitivity
                                        )
            else:
                spectrum = SecondarySpectrum(counts=counts_num,
                                             realtime=realtime,
                                             livetime=livetime,
                                             ecal=ecal,
                                             classcode=classcode
                                             )
            yield spectrum
        except:
            yield None

def readSpectrumFile(filepath, sharedObject, tstatus, requireRASESen=True, only_one_secondary=True):
    """
    Reads in the Spectrum File
    :param filepath: path to spectrum file
    :param sharedObject: contains fields that are set during parsing of the file
    :param tstatus: information string that is augmented during parcing of the file
    :return: counts, ecal, realtime, livetime, sensitivity, countsBckg, ecalBckg, realtimeBckg, livetimeBckg
    """
    try:
        specElement = None
        specElementBckg = None
        # First strip all namespaces if any
        # TODO: make this a general utility method as it can be useful elsewhere

        root = get_ET_from_file(filepath).getroot()
        # Now extract the relevant details from the file
        measurement = root.find('Measurement')
        rad_measurement = root.find('RadMeasurement')
        if measurement is not None:
            return parseMeasurement(measurement, filepath, sharedObject, tstatus, requireRASESen, only_one_secondary)
        elif rad_measurement is not None:
            return parseRadMeasurement(root, filepath, sharedObject, tstatus, requireRASESen, only_one_secondary)
    except BaseSpectraFormatException as ex:
        message = f"{str(ex)} in file {ntpath.basename(filepath)}"
        tstatus.append(message)
        return None
    except:
        print(sys.exc_info())
    #except : return None


def parseMeasurement(measurement, filepath, sharedObject, tstatus, requireRASESen=True, only_one_secondary=True):
    """
    Pull key data out of older .n42 files
    @param measurement:
    @param filepath:
    @param sharedObject:
    @param tstatus:
    @param requireRASESen:
    @param only_one_secondary:
    @return:
    """
    try:
        specElement = requiredElement('.//Spectrum', measurement)
        allSpectra = measurement.findall("Spectrum")
        if len(allSpectra) > 1:
            sharedObject.bkgndSpectrumInFile = True
            specElementBckg = allSpectra[1]
        if only_one_secondary and (len(allSpectra) > 2):
            raise BaseSpectraFormatException(f'Too many Spectrum elements, expected 1 or 2')

        chanData = requiredElement('.//ChannelData', specElement)
        countsChar = chanData.text.strip("'").strip().split()
        if len(countsChar) < 2:
            countsChar = chanData.text.strip("'").strip().split(',')
        if ("." in countsChar[0]):
            sharedObject.chanDataType = "float"
        else:
            sharedObject.chanDataType = "int"
        counts = [float(count) for count in countsChar]
        if not counts: raise BaseSpectraFormatException('Could not parse ChannelData')
        chanDataBckg = None
        countsBckg = None
        if sharedObject.isBckgrndSave and sharedObject.bkgndSpectrumInFile:
            chanDataBckg = requiredElement('.//ChannelData', specElementBckg, 'secondary spectrum')
            countsChar = chanDataBckg.text.strip("'").strip().split()
            countsBckg = [float(count) for count in countsChar]
            if not countsBckg: raise BaseSpectraFormatException('Could not parse ChannelData (secondary spectrum)')
        # uncompress if needed
        counts = uncompressCountedZeroes(chanData,counts)
        if chanDataBckg is not None:
            countsBckg = uncompressCountedZeroes(chanDataBckg,countsBckg)

        realtimeBckg = None
        livetimeBckg = None
        ecalBckg = None
        calibration = specElement.find('Calibration')
        if calibration is None:
            calibration = requiredElement('.//Calibration', measurement, 'or in Spectrum element')

        calElement = requiredElement('.//Coefficients',requiredElement('.//Equation',calibration))
        ecal = [float(value) for value in calElement.text.split()]
        realtimeElement = requiredElement(('.//RealTime','RealTimeDuration'),specElement)
        realtime = getSeconds(realtimeElement.text.strip())
        livetimeElement = requiredElement(('.//LiveTimeDuration','LiveTime'), specElement)
        livetime = getSeconds(livetimeElement.text.strip())
        if requireRASESen:
            RASEsensElement = requiredSensitivity(('.//RASE_Sensitivity', 'FLUX_Sensitivity'), specElement)
            if RASEsensElement[0] is None:
                rase_sensitivity = 'NaN'
            else:
                rase_sensitivity = float(RASEsensElement[0].text.strip())
            if RASEsensElement[1] is None:
                flux_sensitivity = 'NaN'
            else:
                flux_sensitivity = float(RASEsensElement[1].text.strip())
        else:
            rase_sensitivity = flux_sensitivity = 'NaN'

        if chanDataBckg is not None:
            ecalBckg = []
            calibrationBckg = specElementBckg.find('Calibration')
            if calibrationBckg is not None:
                calElement = requiredElement('.//Coefficients', requiredElement('.//Equation', calibrationBckg))
                ecalBckg = [float(value) for value in calElement.text.split()]
            else:
                message = "no Background Calibration in file " + ntpath.basename(filepath)
                tstatus.append(message)
            realtimeElementBckg = requiredElement(('.//RealTime','RealTimeDuration'), specElementBckg, 'secondary spectrum')
            realtimeBckg = getSeconds(realtimeElementBckg.text.strip())
            livetimeElementBckg = requiredElement(('.//LiveTimeDuration','LiveTime'), specElementBckg, 'secondary spectrum')
            livetimeBckg = getSeconds(livetimeElementBckg.text.strip())

        return counts, ecal, realtime, livetime, rase_sensitivity, flux_sensitivity, \
                    countsBckg, ecalBckg, realtimeBckg, livetimeBckg

    except BaseSpectraFormatException as ex:
        message = f"{str(ex)} in file {ntpath.basename(filepath)}"
        tstatus.append(message)
        return None


def parseRadMeasurement(root, filepath, sharedObject, tstatus, requireRASESens, only_one_secondary=True ):
    """
    Pull key data out of 2012 .n42 files
    @param root:
    @param filepath:
    @param sharedObject:
    @param tstatus:
    @param requireRASESens:
    @param only_one_secondary:
    @return:
    """
    try:
        radElement = requiredElement('.//RadMeasurement', root, )
        allRad = root.findall("RadMeasurement")
        if len(allRad) > 1:
            sharedObject.bkgndSpectrumInFile = True
            radElementBckg = allRad[1]
        if (len(allRad) > 2) and only_one_secondary:
            raise BaseSpectraFormatException(f'Too many RadMeasurement elements, expected 1 or 2')
        specElement = requiredElement('.//Spectrum', radElement)
        chanData = requiredElement('.//ChannelData', specElement)
        countsChar = chanData.text.strip("'").strip().split()
        if len(countsChar) < 2:
            countsChar = chanData.text.strip("'").strip().split(',')
        counts = [float(count) for count in countsChar]
        if not counts: raise BaseSpectraFormatException('Could not parse ChannelData')
        if ("." in countsChar[0]):
            sharedObject.chanDataType = "float"
        else:
            sharedObject.chanDataType = "int"
        counts = ','.join(map(str, counts))
        chanDataBckg = None
        countsBckg = None
        if sharedObject.isBckgrndSave and sharedObject.bkgndSpectrumInFile:
            specElementBckg = requiredElement('.//Spectrum', radElementBckg, 'secondary spectrum')
            chanDataBckg = requiredElement('.//ChannelData', specElementBckg, 'secondary spectrum')
            countsChar = chanDataBckg.text.strip("'").strip().split()
            countsBckg = [float(count) for count in countsChar]
            if not counts: raise BaseSpectraFormatException('Could not parse ChannelData in secondary spectrum')
            countsBckg = ','.join(map(str, countsBckg))
        realtimeBckg = None
        livetimeBckg = None
        ecalBckg = None
        rase_sensitivity = None
        flux_sensitivity = None
        calibration = requiredElement('.//EnergyCalibration',root)
        calElement = requiredElement('.//CoefficientValues',calibration)
        ecal = [float(value) for value in calElement.text.split()]
        realtimeElement = requiredElement(('.//RealTime','.//RealTimeDuration'),radElement)
        realtime = getSeconds(realtimeElement.text.strip())
        livetimeElement = requiredElement(('.//LiveTimeDuration','.//LiveTime'),specElement)
        livetime = getSeconds(livetimeElement.text.strip())
        if requireRASESens:
            RASEsensElement = requiredSensitivity(('.//RASE_Sensitivity', './/FLUX_Sensitivity'), specElement)
        else:
            RASEsensElement = specElement.find('Calibration')    # TODO: is this a problem for flux mode?
        if RASEsensElement is not None:
            if RASEsensElement[0] is None:
                rase_sensitivity = 'NaN'
            else:
                rase_sensitivity = float(RASEsensElement[0].text.strip())
            if RASEsensElement[1] is None:
                flux_sensitivity = 'NaN'
            else:
                flux_sensitivity = float(RASEsensElement[1].text.strip())
        if chanDataBckg is not None:
            ecalBckg = ecal
            realtimeElementBckg = requiredElement(('.//RealTime','.//RealTimeDuration'),radElementBckg,'secondary spectrum')
            realtimeBckg = getSeconds(realtimeElementBckg.text.strip())
            livetimeElementBckg = requiredElement(('.//LiveTimeDuration','.//LiveTime'), specElementBckg, 'secondary spectrum')
            livetimeBckg = getSeconds(livetimeElementBckg.text.strip())
        return counts, ecal, realtime, livetime, rase_sensitivity, flux_sensitivity, countsBckg, ecalBckg, \
               realtimeBckg, livetimeBckg
    except BaseSpectraFormatException as ex:
        message = f"{str(ex)} in file {ntpath.basename(filepath)}"
        tstatus.append(message)
        return None


def requiredElement(element, source, extratext=''):
    if isinstance(element, str):
        el = source.find(element)
    else:
        for thiselement in element:
            el = source.find(f"{thiselement}")
            if el is not None: return el
    if extratext: extratext = f'({extratext})'
    if el is None:
        raise BaseSpectraFormatException(f'No {element} in element {source.tag} {extratext}')
    return el


def requiredSensitivity(element, source):
    """
    Checks to see if RASE_Sensitvity and FLUX_Sensitivity terms are in a loaded spectrum.
    If not, return None for that specific sensitivity value. If it is None, that spectrum
    will not appear in the list of base spectra for that detector when creating a scenario,
    and it will show as red in the scenario list
    """
    if isinstance(element[0], str):
        el = [source.find(f"{element[0]}")]
    else:
        el = [None]
    if isinstance(element[1], str):
        el.append(source.find(f"{element[1]}"))
    else:
        el.append(None)
    if el == [None, None]:
        raise BaseSpectraFormatException(f'No {element[0]} or {element[1]} in element {source.tag}')
    return el