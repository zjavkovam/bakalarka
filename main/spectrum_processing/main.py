import nmrglue as ng
import matplotlib
import numpy as np
matplotlib.use('TkAgg')
matplotlib.use('agg')
import matplotlib.pyplot as plt
from main.models import *

def load_data_B(path):
    dic, data = ng.bruker.read(path)
    data = ng.bruker.remove_digital_filter(dic, data)

    # process the spectrum
    data = ng.proc_base.zf_size(data, 32768)  # zero fill to 32768 points
    data = ng.proc_base.fft(data)  # Fourier transform
    data = ng.proc_autophase.autops(data, 'peak_minima')  # phase correction
    data = ng.proc_base.di(data)  # discard the imaginaries
    data = ng.proc_base.rev(data)  # reverse the data
    return [dic, data]


def load_data_V(name):
    # dir_name = '/Users/mnk/Downloads/NMR FIIT/JN-99 - 6-NH2-BTZ-2-Me/jn99-1A_20190528_01/PROTON_01.fid' # directory where the Varian data is held.
    dic, data = ng.varian.read(name, procpar_file='procpar')

    udic = ng.varian.guess_udic(dic, data)
    udic[0]['complex'] = True
    udic[0]['encoding'] = 'direct'
    udic[0]['sw'] = float(dic["procpar"]["sw"]["values"][0])
    udic[0]['obs'] = float(dic["procpar"]["reffrq"]["values"][0])
    udic[0]['car'] = float(dic["procpar"]["sw"]["values"][0]) / 2 - float(dic["procpar"]["rfl"]["values"][0])
    udic[0]['label'] = '1H'

    C = ng.convert.converter()
    C.from_varian(dic, data, udic)
    pdic, pdata = C.to_pipe()

    pdic, pdata = ng.pipe_proc.sp(pdic, pdata, off=0.35, end=0.98, pow=2, c=1.0)
    pdic, pdata = ng.pipe_proc.zf(pdic, pdata, auto=True)
    pdic, pdata = ng.pipe_proc.ft(pdic, pdata, auto=True)
    pdata = ng.proc_autophase.autops(pdata, 'peak_minima')
    pdic, pdata = ng.pipe_proc.di(pdic, pdata)

    return dic, pdic, pdata


def delete_impurity(integral_list, solvent):
    solvent = Solvent.objects.get(name=solvent)
    impurities = Impurity.objects.filter(solvent=solvent)


    for impurity in impurities:
        position = impurity.position
        
        for peak_position in list(integral_list.keys()):
            if abs(peak_position - float(position)) < 0.05 or abs(peak_position - float(solvent.position)) < 0.05:
                del integral_list[peak_position] 

    return integral_list


def draw_integrals(integral_list, data, ppm_scale, ax):
    for i in integral_list:
        start = int(integral_list[i][0])
        end = int(integral_list[i][1])
        # extract the peak
        peak = data[start:end + 1]
        peak_scale = ppm_scale[start:end + 1]

        # plot the integration lines, limits and name of peaks
        ax.plot(peak_scale, peak.cumsum() / 100. + peak.max())
        ax.plot(peak_scale, [0] * len(peak_scale))
        ax.text(peak_scale[0], 0.5 * peak.sum() / 100. + peak.max(), round(integral_list[i][2], 2), fontsize=10)


def find_ratios(integral_list, H):
    # ppm: b,e,area 

    maximum = max(integral_list.values(), key=lambda x: x[2])[2]

    if H != '':
        for position, value in integral_list.items():
            if float(H) == position:
                peak_area = value[2]
                for pos,val in integral_list.items():
                    integral_list[pos][2] = round(val[2]/ peak_area, 2)
                break
    else:
        for pos,val in integral_list.items():
            integral_list[pos][2] = round(val[2]/ maximum, 2)
    return integral_list


def integration(data, peak_table, peak_locations_ppm):
    list = {}
    for peak_number in range(len(peak_locations_ppm) - 1):
        loc_ppm = peak_locations_ppm[peak_number]
        loc_pts = int(peak_table['X_AXIS'][peak_number]) # begining of peak
        fwhm = peak_table['X_LW'][peak_number]  #full width at half maximum
        hwhm_int = int(np.floor(fwhm / 2.)) 
        peak_area = data[loc_pts - hwhm_int: loc_pts + hwhm_int + 1].sum() 

        list[round(loc_ppm,2)] = [loc_pts - hwhm_int, loc_pts + hwhm_int + 1, peak_area, ' ']
    return list


def delete_splits(peaks):
    new = {}
    peaks = dict(sorted(peaks.items(), key=lambda x: x[1][2])) 

    if len(peaks) == 1:
        return peaks
    
    max_position = list(peaks.keys())[-1]
    for index, position in enumerate(peaks.keys()):
        if  (peaks[position][2] / peaks[max_position][2]) > 0.2:
            new[position] = peaks[position]

    new = dict(sorted(new.items()))
    return new    

def get_multiplicity(peaks, new_element):
    peaks = delete_splits(peaks)
    keys = list(peaks.keys())  

    if len(peaks) == 1:
        multiplicity = 's'
    elif len(peaks) == 2:
        if 0.9 < (peaks[keys[0]][2]/peaks[keys[1]][2]) < 1.1:
            multiplicity = 'd'
        else:
            multiplicity = 'm'
    elif len(peaks) == 3 :
        if 1.4 < peaks[keys[0]][2] / peaks[keys[1]][2] < 1.6 and 0.9 < peaks[keys[0]][2] / peaks[keys[2]][2] < 1.1:
            multiplicity = 't'
        else:
            multiplicity = 'm'
    elif len(peaks) == 4:
        if 0.9 < (peaks[keys[0]][2]/peaks[keys[1]][2]) < 1.1 and  0.9 < (peaks[keys[2]][2]/peaks[keys[3]][2]) < 1.1 and  0.9 < (peaks[keys[0]][2]/peaks[keys[2]][2]) < 1.1:
            multiplicity = 'dd'
        elif 1.4 < (peaks[keys[0]][2]/peaks[keys[1]][2]) < 1.6 and  0.9 < (peaks[keys[2]][2]/peaks[keys[3]][2]) < 1.1 and  1.4 < (peaks[keys[0]][2]/peaks[keys[2]][2]) < 1.6:
            multiplicity = 'q'
        else:
            multiplicity = 'm'
    else:
        multiplicity = 'm'
    new_element[3] = multiplicity
    return new_element


def join_close(type, uc, integral_list):
    new = {}
    new_position = list(integral_list.keys())[0]
    new_element = integral_list[new_position]
    max_peak_value = new_element[2]
    max_peak_position = new_position

    joined_peaks = {new_position:new_element} # for multiplicity 
    for index, position in enumerate(integral_list.keys()):
        # Prevent going out of index
        if index < len(integral_list.keys()) - 1:
            #chemical shifts in ppm 
            next_position = list(integral_list.keys())[index+1]

            # Calculate the distance between the first two peaks
            peak1 = uc.i(str (position) + ' ppm')  
            peak2 = uc.i(str (next_position) + ' ppm')

            if type == 'b':
                peak1, peak2 = peak1/4, peak2/4
            else:
                peak1, peak2 = peak1/8, peak2/8

            distance = abs(peak2 - peak1)
            if distance <= 20:
            #if abs(position-next_position) < 0.05: 
                #merge 
                next_element = integral_list[next_position]
                joined_peaks[next_position] =  next_element
                
                new_area = new_element[2] + next_element[2]                  
                if integral_list[next_position][2] > max_peak_value:
                    max_peak_position = next_position
                    max_peak_value = integral_list[next_position][2]
                new_element = [min(new_element[0], next_element[0]), max(new_element[1], next_element[1]), new_area, ' ']            
            else:
                #add to list 
                new_element = get_multiplicity(joined_peaks, new_element)
                new[max_peak_position] = new_element
                
                #reset values
                new_position = next_position
                new_element = integral_list[next_position]
                max_peak_value = new_element[2]
                max_peak_position = new_position
                joined_peaks = {new_position: new_element}

    new[max_peak_position] = new_element
    return new


def draw_plot(peak_locations_ppm, peak_amplitudes, ppm_scale, data, fig, ax, parameters, th):
    #peak marking
    if parameters["show_peaks"]:
        ax.plot(peak_locations_ppm, peak_amplitudes, 'ro')

    #threshold line
    if parameters["show_threshold"]:
        ax.hlines(th, xmin=0, xmax=100, linestyle="--", color="k")

    ax.plot(ppm_scale, data, "k-")
    ax.invert_xaxis()
 
    ax.set_xlim(float(parameters["ppm_end"]), float(parameters["ppm_start"]))
    #ax.set_xlim(9,7)
    ax.set_xlabel('PPM')
    fig.savefig('./main/static/figure_nmrglue.png')
  

def clean(integral_list, threshold, ppm):
    new = {}
    for pos, val in integral_list.items():
        new[pos] = val
        if val[2] == 0:
            del new[pos]

        elif threshold and val[2] < float(threshold):
            del new[pos]

        elif ppm and pos == float(ppm):
            del new[pos] 


    return new


def format_spectrum(integral_list):
    new = []
    for i in integral_list:
        new.append(str(round(i, 2)) + " ( "+ integral_list[i][3] + ", " + str(integral_list[i][2]) + "H)")

    return new

def save_spectrum(spectrum, integral_list, solvent, name, H):
    if H != '':
        integral_list = find_ratios(integral_list, '')

    user = User.objects.filter(name=name).first()
    if user is None:
        user = User(name=name)
        user.save()

    # Create a new solvent instance
    try:
        solvent = Solvent.objects.get(name=solvent)
    except Solvent.DoesNotExist:
        return -1

    # Create a new compounds instance
    compound = Compound.objects.filter(name="Unknown").first()

    # Check if the spectrum already exists
    spec = Spectrum.objects.filter(user=user, compound=compound, formated=spectrum).first()

    if spec is None:
        # Create a new spectrum instance
        spec = Spectrum(user=user, solvent=solvent, compound=compound, formated=spectrum)
        spec.save()

        # Create peaks for the spectrum
        for peak_position, peak_area in integral_list.items():
            peak = Peak(spectrum=spec, ppm=peak_position, integral_area=peak_area[2])
            print(peak.integral_area)
            peak.save()

    return spec

def main(uploaded_files, parameters):
    #parameters = [instrument_type, threshold_num, ppm_start, ppm_end, show_integrals, show_peaks, show_thresholds, 1H, max-ratio, name, delete_threshold, delete_ppm]
    vdic = 0
    type =''
    if parameters["type"] == "varian" or (parameters["type"] == "auto" and len(uploaded_files) == 4):
        vdic, dic, data = load_data_V("media")
        solvent = vdic["procpar"]['solvent']["values"][0]
        # conversion to ppm
        uc = ng.pipe.make_uc(dic, data)
        ppm_scale = uc.ppm_scale()
        type = 'v'

    else:
        dic, data = load_data_B("media")
        solvent = dic['acqus']['SOLVENT'].lower()

        # conversion to ppm
        udic = ng.bruker.guess_udic(dic, data)
        uc = ng.fileiobase.uc_from_udic(udic)
        ppm_scale = uc.ppm_scale()
        type = 'b'
   

    fig = plt.figure()
    ax = fig.add_subplot(111)

    #peak picking
    # Calculate the baseline noise level using the MAD method
    baseline = np.median(np.abs(data - np.median(data)))
    noise_level = 1.4826 * baseline  # 1.4826 is a scaling factor for MAD

    # Set the threshold to a multiple of the noise level
    threshold = int(parameters['threshold_num']) * noise_level 
    peak_table = ng.peakpick.pick(data, pthres=threshold, algorithm='downward')

    #SORT
    sorted_indices = peak_table['X_AXIS'].argsort()
    peak_table = peak_table[sorted_indices]

    #Get peak locations and amplitudes
    peak_locations_ppm = [uc.ppm(i) for i in peak_table['X_AXIS']]
    peak_amplitudes = data[peak_table['X_AXIS'].astype('int')]

    #integrals
    integral_list = integration(data, peak_table, peak_locations_ppm)

    #Join close peaks 
    integral_list = join_close(type,uc, integral_list)

    #Delete impurities and solvent
    integral_list = delete_impurity(integral_list, solvent)

    #ratios of integrals
    integral_list = find_ratios(integral_list, parameters['1H'])

    integral_list = clean(integral_list, parameters['delete_threshold'], parameters['delete_ppm'])
    #draw integrals
    if parameters["show_integrals"]:
        draw_integrals(integral_list, data, ppm_scale, ax)

    #draww plot
    draw_plot(peak_locations_ppm, peak_amplitudes, ppm_scale, data, fig, ax, parameters, threshold)

    formated = format_spectrum(integral_list)
    spec = save_spectrum(formated, integral_list, solvent, parameters['name'], parameters['1H'])
    return spec

