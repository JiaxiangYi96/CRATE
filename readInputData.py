#
# Input Data Reader Module (UNNAMED Program)
# ==========================================================================================
# Summary:
# ...
# ------------------------------------------------------------------------------------------
# Development history:
# Bernardo P. Ferreira | January 2020 | Initial coding.
# ==========================================================================================
#                                                                             Import modules
# ==========================================================================================
# Operating system related functions
import os
# Import from string
import importlib
# Operations on files and directories
import shutil
# Working with arrays
import numpy as np
# Shallow and deep copy operations
import copy
# Display messages
import info
# Regular expressions
import re
# Read specific lines from file
import linecache
# Inspect file name and line
import inspect
# Extract information from path
import ntpath
# Display errors, warnings and built-in exceptions
import errors
# Manage files and directories
import fileOperations
# Packager
import packager
# Links interface
import LinksInterface
# Material interface
import material.materialInterface
#
#                                                             Check input validity functions
# ==========================================================================================
# Check if a given input is or represents a number (either integer or floating-point)
def checkNumber(x):
    isNumber = True
    try:
        float(x)
        return isNumber
    except ValueError:
        isNumber = False
        return isNumber
# ------------------------------------------------------------------------------------------
# Check if a given input is a positive integer
def checkPositiveInteger(x):
    isPositiveInteger = True
    if isinstance(x,int) or isinstance(x,np.integer):
        if x <= 0:
            isPositiveInteger = False
    elif not re.match('^[1-9][0-9]*$',str(x)):
        isPositiveInteger = False
    return isPositiveInteger
# ------------------------------------------------------------------------------------------
# Check if a given input contains only letters, numbers or underscores
def checkValidName(x):
    isValid = True
    if not re.match('^[A-Za-z0-9_]+$',str(x)):
        isValid = False
    return isValid
#
#                                                                           Search functions
# ==========================================================================================
# Find the line number where a given keyword is specified in a file
def searchKeywordLine(file,keyword):
    file.seek(0)
    line_number = 0
    for line in file:
        line_number = line_number + 1
        if keyword in line and line.strip()[0]!='#':
            return line_number
    location = inspect.getframeinfo(inspect.currentframe())
    errors.displayError('E00003',location.filename,location.lineno+1,keyword)
# ------------------------------------------------------------------------------------------
# Search for a given keyword in a file. If the keyword is found, the line number is returned
def searchOptionalKeywordLine(file,keyword):
    isFound = False
    file.seek(0)
    line_number = 0
    for line in file:
        line_number = line_number + 1
        if keyword in line and line.strip()[0]!='#':
            isFound = True
            return [isFound,line_number]
    return [isFound,line_number]
#
#                                                                       Read input data file
# ==========================================================================================
# Read the input data file
def readInputData(input_file,dirs_dict):
    # Get input file and problem directory and path data
    input_file_path = dirs_dict['input_file_path']
    problem_dir = dirs_dict['problem_dir']
    postprocess_dir = dirs_dict['postprocess_dir']
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read strain formulation
    keyword = 'Strain_Formulation'
    max = 2
    strain_formulation = readTypeAKeyword(input_file,input_file_path,keyword,max)
    # Large strain formulation has not been implemented yet
    if strain_formulation == 2:
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayError('E00016',location.filename,location.lineno+1)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read problem type and set problem dimensions
    keyword = 'Problem_Type'
    max = 4
    problem_type = readTypeAKeyword(input_file,input_file_path,keyword,max)
    n_dim,comp_order_sym,comp_order_nsym = setProblemTypeParameters(problem_type)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read RVE dimensions
    keyword = 'RVE_Dimensions'
    rve_dims = readRVEDimensions(input_file,input_file_path,keyword,n_dim)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read number of material phases and the associated constitutive models and properties
    keyword = 'Material_Phases'
    n_material_phases,material_phases_models,material_properties = \
                                  readMaterialProperties(input_file,input_file_path,keyword)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read macroscale loading
    keyword = 'Macroscale_Loading'
    max = 3
    mac_load_type = readTypeAKeyword(input_file,input_file_path,keyword,max)
    mac_load,mac_load_presctype = \
                             readMacroscaleLoading(input_file,input_file_path,mac_load_type,
                                                   strain_formulation,n_dim,comp_order_nsym)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read self consistent scheme (optional). If the associated keyword is not found, then
    # a default specification is assumed
    keyword = 'Self_Consistent_Scheme'
    isFound,keyword_line_number = searchOptionalKeywordLine(input_file,keyword)
    if isFound:
        max = 2
        self_consistent_scheme = readTypeAKeyword(input_file,input_file_path,keyword,max)
    else:
        self_consistent_scheme = 2
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read self consistent scheme maximum number of iterations (optional). If the associated
    # keyword is not found, then a default specification is assumed
    keyword = 'SCS_Max_Number_of_Iterations'
    isFound,keyword_line_number = searchOptionalKeywordLine(input_file,keyword)
    if isFound:
        max = '~'
        scs_max_n_iterations = readTypeAKeyword(input_file,input_file_path,keyword,max)
    else:
        scs_max_n_iterations = 20
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read self consistent scheme convergence tolerance (optional). If the associated
    # keyword is not found, then a default specification is assumed
    keyword = 'SCS_Convergence_Tolerance'
    isFound,keyword_line_number = searchOptionalKeywordLine(input_file,keyword)
    if isFound:
        max = '~'
        scs_conv_tol = readTypeBKeyword(input_file,input_file_path,keyword)
    else:
        scs_conv_tol = 1e-6
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read clustering method
    keyword = 'Clustering_Method'
    max = 1
    clustering_method = readTypeAKeyword(input_file,input_file_path,keyword,max)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read clustering strategy (optional). If the associated keyword is not found, then a
    # default specification is assumed
    keyword = 'Clustering_Strategy'
    isFound,keyword_line_number = searchOptionalKeywordLine(input_file,keyword)
    if isFound:
        max = 1
        clustering_strategy = readTypeAKeyword(input_file,input_file_path,keyword,max)
    else:
        clustering_strategy = 1
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read clustering solution method (optional). If the associated keyword is not found,
    # then a default specification is assumed
    keyword = 'Clustering_Solution_Method'
    isFound,keyword_line_number = searchOptionalKeywordLine(input_file,keyword)
    if isFound:
        max = 2
        clustering_solution_method = \
                                    readTypeAKeyword(input_file,input_file_path,keyword,max)
    else:
        clustering_solution_method = 1
    # Read clustering solution method parameters
    Links_dict = ()
    if clustering_solution_method == 2:
        # Check if all materials have material source 2!!
        for mat_phase in material_properties.keys():
            if material_phases_models[mat_phase]['source'] != 2:
                location = inspect.getframeinfo(inspect.currentframe())
                errors.displayError('E00067',location.filename,location.lineno+1)
        # Build Links dictionary
        Links_dict = LinksInterface.readLinksParameters(input_file,input_file_path,
                            problem_type,checkNumber,checkPositiveInteger,searchKeywordLine,
                                                                  searchOptionalKeywordLine)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read number of cluster associated to each material phase
    keyword = 'Number_of_Clusters'
    phase_n_clusters = readPhaseClustering(input_file,input_file_path,keyword,
                                                      n_material_phases,material_properties)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read number of load increments
    keyword = 'Number_of_Load_Increments'
    max = '~'
    n_load_increments = readTypeAKeyword(input_file,input_file_path,keyword,max)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read maximum number of iterations to solve each load increment (optional). If the
    # associated keyword is not found, then a default specification is assumed
    keyword = 'Max_Number_of_Iterations'
    isFound,keyword_line_number = searchOptionalKeywordLine(input_file,keyword)
    if isFound:
        max = '~'
        max_n_iterations = readTypeAKeyword(input_file,input_file_path,keyword,max)
    else:
        max_n_iterations = 20
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read convergence tolerance to solve each load increment (optional). If the associated
    # keyword is not found, then a default specification is assumed
    keyword = 'Convergence_Tolerance'
    isFound,keyword_line_number = searchOptionalKeywordLine(input_file,keyword)
    if isFound:
        conv_tol = readTypeBKeyword(input_file,input_file_path,keyword)
    else:
        conv_tol = 1e-6
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read maximum level of subincrementation allowed (optional). If the associated
    # keyword is not found, then a default specification is assumed
    keyword = 'Max_SubIncrem_Level'
    isFound,keyword_line_number = searchOptionalKeywordLine(input_file,keyword)
    if isFound:
        max = '~'
        max_subincrem_level = readTypeAKeyword(input_file,input_file_path,keyword,max)
    else:
        max_subincrem_level = 5
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read material state update maximum number of iterations (optional). If the associated
    # keyword is not found, then a default specification is assumed
    keyword = 'SU_Max_Number_of_Iterations'
    isFound,keyword_line_number = searchOptionalKeywordLine(input_file,keyword)
    if isFound:
        max = '~'
        su_max_n_iterations = readTypeAKeyword(input_file,input_file_path,keyword,max)
    else:
        su_max_n_iterations = 20
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read material state update convergence tolerance (optional). If the associated
    # keyword is not found, then a default specification is assumed
    keyword = 'SU_Convergence_Tolerance'
    isFound,keyword_line_number = searchOptionalKeywordLine(input_file,keyword)
    if isFound:
        su_conv_tol = readTypeBKeyword(input_file,input_file_path,keyword)
    else:
        su_conv_tol = 1e-6
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read the spatial discretization file absolute path
    keyword = 'Discretization_File'
    valid_exts = ['.rgmsh']
    discret_file_path = \
                   readDiscretizationFilePath(input_file,input_file_path,keyword,valid_exts)
    # Copy the spatial discretization file to the problem directory and update the absolute
    # path to the copied file
    try:
        shutil.copy2(discret_file_path,problem_dir+ntpath.basename(discret_file_path))
        discret_file_path = problem_dir+ntpath.basename(discret_file_path)
    except IOError as message:
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayException(location.filename,location.lineno+1,message)
    # Store spatial discretization file absolute path
    dirs_dict['discret_file_path'] = discret_file_path
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read VTK output options
    keyword = 'VTK_Output'
    isFound,keyword_line_number = searchOptionalKeywordLine(input_file,keyword)
    if isFound:
        is_VTK_output = True
        vtk_format,vtk_inc_div,vtk_vars = \
                      readVTKOptions(input_file,input_file_path,keyword,keyword_line_number)
        # Create VTK folder in post processing directory
        fileOperations.makeDirectory(postprocess_dir + 'VTK/','overwrite')
    else:
        is_VTK_output = False
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Package problem general data
    info.displayInfo('5','Packaging problem general data...')
    problem_dict = packager.packageProblem(strain_formulation,problem_type,n_dim,
                                                             comp_order_sym,comp_order_nsym)
    # Package data associated to the material phases
    info.displayInfo('5','Packaging material data...')
    mat_dict = packager.packageMaterialPhases(n_material_phases,material_phases_models,
                                                                        material_properties)
    # Package data associated to the macroscale loading
    info.displayInfo('5','Packaging macroscale loading data...')
    macload_dict = packager.packageMacroscaleLoading(mac_load_type,mac_load,
                                                       mac_load_presctype,n_load_increments)
    # Package data associated to the spatial discretization file(s)
    info.displayInfo('5','Packaging regular grid data...')
    rg_dict = packager.packageRegularGrid(discret_file_path,rve_dims,mat_dict,problem_dict)
    # Package data associated to the clustering
    info.displayInfo('5','Packaging clustering data...')
    clst_dict = packager.packageRGClustering(clustering_method,clustering_strategy,
                             clustering_solution_method,Links_dict,phase_n_clusters,rg_dict)
    # Package data associated to the self-consistent scheme
    info.displayInfo('5','Packaging self-consistent scheme data...')
    scs_dict = packager.packageSCS(self_consistent_scheme,scs_max_n_iterations,scs_conv_tol)
    # Package data associated to the self-consistent scheme
    info.displayInfo('5','Packaging algorithmic data...')
    algpar_dict = packager.packageAlgorithmicParameters(max_n_iterations,conv_tol,
                                        max_subincrem_level,su_max_n_iterations,su_conv_tol)
    # Package data associated to the VTK output
    info.displayInfo('5','Packaging VTK output data...')
    if is_VTK_output:
        vtk_dict = packager.packageVTK(is_VTK_output,vtk_format,vtk_inc_div,vtk_vars)
    else:
        vtk_dict = packager.packageVTK(is_VTK_output)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    return [problem_dict,mat_dict,macload_dict,rg_dict,clst_dict,scs_dict,algpar_dict,
                                                                                   vtk_dict]
#
#                                                                  Read input data functions
# ==========================================================================================
# Read a keyword of type A specification, characterized as follows:
#
# < keyword > < positive integer >
#
def readTypeAKeyword(file,file_path,keyword,max):
    keyword_line_number = searchKeywordLine(file,keyword)
    line = linecache.getline(file_path,keyword_line_number).split()
    if len(line) == 1:
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayError('E00007',location.filename,location.lineno+1,keyword)
    elif not checkPositiveInteger(line[1]):
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayError('E00007',location.filename,location.lineno+1,keyword)
    elif isinstance(max,int):
        if int(line[1]) > max:
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayError('E00007',location.filename,location.lineno+1,keyword)
    return int(line[1])
# ------------------------------------------------------------------------------------------
# Read a keyword of type B specification, characterized as follows:
#
# < keyword >
# < non-negative floating-point number >
#
def readTypeBKeyword(file,file_path,keyword):
    keyword_line_number = searchKeywordLine(file,keyword)
    line = linecache.getline(file_path,keyword_line_number+1).split()
    if line == '':
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayError('E00004',location.filename,location.lineno+1,keyword)
    elif len(line) != 1:
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayError('E00004',location.filename,location.lineno+1,keyword)
    elif not checkNumber(line[0]) or float(line[0]) <= 0:
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayError('E00004',location.filename,location.lineno+1,keyword)
    return float(line[0])
# ------------------------------------------------------------------------------------------
# Read the number of material phases and associated properties of the general heterogeneous
# material specified as follows:
#
# Material_Phases < n_material_phases >
# < phase_id > < model_name > < n_properties > [ < model_source > ]
# < property1_name > < value >
# < property2_name > < value >
# < phase_id > < model_name > < n_properties > [ < model_source > ]
# < property1_name > < value >
# < property2_name > < value >
# ...
#
# Store the material phases properties in a dictionary as
#
#    dictionary['phase_id'] = {'property1_name': value, 'property2_name': value, ...}
#
# and the material phases constitutive models in a dictionary as
#
#    dictionary['phase_id'] = {'name': model_name, 'source': model_source,
#                              'suct_function': suct_function()}
#
def readMaterialProperties(file,file_path,keyword):
    keyword_line_number = searchKeywordLine(file,keyword)
    line = linecache.getline(file_path,keyword_line_number).split()
    if len(line) == 1:
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayError('E00052',location.filename,location.lineno+1,keyword)
    elif not checkPositiveInteger(line[1]):
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayError('E00052',location.filename,location.lineno+1,keyword)
    # Set number of material phases
    n_material_phases = int(line[1])
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Initialize material phases properties and constitutive models dictionaries
    material_properties = dict()
    material_phases_models = dict()
    # Loop over material phases
    line_number = keyword_line_number + 1
    for i in range(n_material_phases):
        phase_header = linecache.getline(file_path,line_number).split()
        if phase_header[0] == '':
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayError('E00005',location.filename,location.lineno+1,keyword,i+1)
        elif len(phase_header) not in [3,4]:
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayError('E00005',location.filename,location.lineno+1,keyword,i+1)
        elif not checkPositiveInteger(phase_header[0]):
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayError('E00005',location.filename,location.lineno+1,keyword,i+1)
        elif phase_header[0] in material_properties.keys():
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayError('E00005',location.filename,location.lineno+1,keyword,i+1)
        # Set material phase
        mat_phase = str(phase_header[0])
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Set material phase constitutive model source
        material_phases_models[mat_phase] = dict()
        if len(phase_header) == 3:
            # If the material phase constitutive model source has not been specified, then
            # assume UNNAMED material procedures by default
            model_source = 1
            material_phases_models[mat_phase]['source'] = model_source
        elif len(phase_header) == 4:
            # Set constitutive model source
            if not checkPositiveInteger(phase_header[3]):
                location = inspect.getframeinfo(inspect.currentframe())
                errors.displayError('E00053',location.filename,location.lineno+1,keyword,
                                                                                  mat_phase)
            elif int(phase_header[3]) not in [1,2,3]:
                location = inspect.getframeinfo(inspect.currentframe())
                errors.displayError('E00053',location.filename,location.lineno+1,keyword,
                                                                                  mat_phase)
            model_source = int(phase_header[3])
            material_phases_models[mat_phase]['source'] = model_source
            # Model source 3 is not implemented yet...
            if model_source in [3,]:
                location = inspect.getframeinfo(inspect.currentframe())
                errors.displayError('E00054',location.filename,location.lineno+1,mat_phase)
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Set material phase constitutive model and associated procedures
        available_mat_models = \
                     material.materialInterface.getAvailableConstitutiveModels(model_source)
        if phase_header[1] not in available_mat_models:
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayError('E00055',location.filename,location.lineno+1,mat_phase,
                                                                               model_source)
        model_name = phase_header[1]
        material_phases_models[mat_phase]['name'] = model_name
        if model_source == 1:
            model_module = importlib.import_module('material.models.' + str(model_name))
            # Set material constitutive model required procedures
            req_procedures = ['setRequiredProperties','init','suct']
            # Check if the material constitutive model required procedures are available
            for procedure in req_procedures:
                if hasattr(model_module,procedure):
                    # Get material constitutive model procedures
                    material_phases_models[mat_phase][procedure] = \
                                                             getattr(model_module,procedure)
                else:
                    location = inspect.getframeinfo(inspect.currentframe())
                    errors.displayError('E00056',location.filename,location.lineno+1,
                                                                       model_name,procedure)
        elif model_source == 2:
            # Get material constitutive model procedures
            setRequiredProperties,writeMaterialProperties = \
                                          LinksInterface.LinksMaterialProcedures(model_name)
            material_phases_models[mat_phase]['setRequiredProperties'] = \
                                                                       setRequiredProperties
            material_phases_models[mat_phase]['writeMaterialProperties'] = \
                                                                     writeMaterialProperties
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        required_properties = material_phases_models[mat_phase]['setRequiredProperties']()
        n_required_properties = len(required_properties)
        if not checkPositiveInteger(phase_header[2]):
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayError('E00005',location.filename,location.lineno+1,keyword,i+1)
        elif int(phase_header[2]) != n_required_properties:
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayError('E00058',location.filename,location.lineno+1,
                                       int(phase_header[2]),mat_phase,n_required_properties)
        n_properties = int(phase_header[2])
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Set material phase properties
        material_properties[mat_phase] = dict()
        for j in range(n_properties):
            property_line = linecache.getline(file_path,line_number+j+1).split()
            if property_line[0] == '':
                location = inspect.getframeinfo(inspect.currentframe())
                errors.displayError('E00006',location.filename,location.lineno+1,
                                                              keyword,j+1,mat_phase)
            elif len(property_line) != 2:
                location = inspect.getframeinfo(inspect.currentframe())
                errors.displayError('E00006',location.filename,location.lineno+1,
                                                              keyword,j+1,mat_phase)
            elif not checkValidName(property_line[0]):
                location = inspect.getframeinfo(inspect.currentframe())
                errors.displayError('E00006',location.filename,location.lineno+1,
                                                              keyword,j+1,mat_phase)
            elif property_line[0] not in required_properties:
                location = inspect.getframeinfo(inspect.currentframe())
                errors.displayError('E00059',location.filename,location.lineno+1,
                                                                 property_line[0],mat_phase)
            elif property_line[0] in material_properties[mat_phase].keys():
                location = inspect.getframeinfo(inspect.currentframe())
                errors.displayError('E00006',location.filename,location.lineno+1,
                keyword,j+1,mat_phase)
            elif not checkNumber(property_line[1]):
                location = inspect.getframeinfo(inspect.currentframe())
                errors.displayError('E00006',location.filename,location.lineno+1,
                                                              keyword,j+1,mat_phase)
            prop_name = str(property_line[0])
            prop_value = float(property_line[1])
            material_properties[mat_phase][prop_name] = prop_value
        line_number = line_number + n_properties + 1
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    return [n_material_phases,material_phases_models,material_properties]
# ------------------------------------------------------------------------------------------
# Read the macroscale loading conditions, specified as
#
#                 2D Problem                                     3D Problem
#   --------------------------------------         --------------------------------------
#   Macroscale_Strain or Macroscale_Stress         Macroscale_Strain or Macroscale_Stress
#   < component_name_11 > < value >                < component_name_11 > < value >
#   < component_name_21 > < value >                < component_name_21 > < value >
#   < component_name_12 > < value >                < component_name_31 > < value >
#   < component_name_22 > < value >                < component_name_12 > < value >
#                                                  < component_name_22 > < value >
#                                                  < component_name_32 > < value >
#                                                  < component_name_13> < value >
#                                                  < component_name_23 > < value >
#                                                  < component_name_33 > < value >
#
#
#   Mixed_Prescription_Index (only if prescribed macroscale strains and stresses)
#   < 0 or 1 > < 0 or 1 > < 0 or 1 > < 0 or 1 > ...
#
# and store them in a dictionary as
#                       _                          _
#                      |'component_name_11' , value |
#    dictionary[key] = |'component_name_21' , value | , where key in ['strain','stress']
#                      |_       ...        ,   ... _|
#
# and in an array(n_dim**2) as
#
#          array = [ < 0 or 1 > , < 0 or 1 > , < 0 or 1 > , < 0 or 1 > , ... ]
#
# Note: The macroscale strain or stress tensor is always assumed to be nonsymmetric and
#       all components must be specified in columnwise order
#
# Note: The symmetry of the macroscale strain and stress tensors is verified under a small
#       strain formulation
#
# Note: Both strain/stress tensor dictionaries and prescription array are then reordered
#       according to the program assumed nonsymmetric component order
#
def readMacroscaleLoading(file,file_path,mac_load_type,strain_formulation,n_dim,
                                                                           comp_order_nsym):
    mac_load = dict()
    if mac_load_type == 1:
        loading_keywords = ['Macroscale_Strain']
        mac_load['strain'] = np.full((n_dim**2,2),'ND',dtype=object)
        mac_load_typeidxs = np.zeros((n_dim**2),dtype=int)
    elif mac_load_type == 2:
        loading_keywords = ['Macroscale_Stress']
        mac_load['stress'] = np.full((n_dim**2,2),'ND',dtype=object)
        mac_load_typeidxs = np.ones((n_dim**2),dtype=int)
    elif mac_load_type == 3:
        loading_keywords = ['Macroscale_Strain','Macroscale_Stress']
        mac_load['strain'] = np.full((n_dim**2,2),'ND',dtype=object)
        mac_load['stress'] = np.full((n_dim**2,2),'ND',dtype=object)
        presc_keyword = 'Mixed_Prescription_Index'
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    for load_keyword in loading_keywords:
        load_keyword_line_number = searchKeywordLine(file,load_keyword)
        for icomponent in range(n_dim**2):
            component_line = linecache.getline(file_path,
                                              load_keyword_line_number+icomponent+1).split()
            if component_line[0] == '':
                location = inspect.getframeinfo(inspect.currentframe())
                errors.displayError('E00008',location.filename,location.lineno+1,
                                                                  load_keyword,icomponent+1)
            elif len(component_line) != 2:
                location = inspect.getframeinfo(inspect.currentframe())
                errors.displayError('E00008',location.filename,location.lineno+1,
                                                                  load_keyword,icomponent+1)
            elif not checkValidName(component_line[0]):
                location = inspect.getframeinfo(inspect.currentframe())
                errors.displayError('E00008',location.filename,location.lineno+1,
                                                                  load_keyword,icomponent+1)
            elif not checkNumber(component_line[1]):
                location = inspect.getframeinfo(inspect.currentframe())
                errors.displayError('E00008',location.filename,location.lineno+1,
                                                                  load_keyword,icomponent+1)
            if load_keyword == 'Macroscale_Strain':
                mac_load['strain'][icomponent,0] = component_line[0]
                mac_load['strain'][icomponent,1] = float(component_line[1])
            elif load_keyword == 'Macroscale_Stress':
                mac_load['stress'][icomponent,0] = component_line[0]
                mac_load['stress'][icomponent,1] = float(component_line[1])
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    if mac_load_type == 3:
        mac_load_typeidxs = np.zeros((n_dim**2),dtype=int)
        presc_keyword_line_number = searchKeywordLine(file,presc_keyword)
        presc_line = linecache.getline(file_path,presc_keyword_line_number+1).split()
        if presc_line[0] == '':
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayError('E00011',location.filename,location.lineno+1,presc_keyword)
        elif len(presc_line) != n_dim**2:
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayError('E00011',location.filename,location.lineno+1,presc_keyword)
        elif not all(presc_line[i] == '0' or presc_line[i] == '1' \
                                                           for i in range(len(presc_line))):
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayError('E00011',location.filename,location.lineno+1,presc_keyword)
        else:
            mac_load_typeidxs = np.array([int(presc_line[i]) \
                                                           for i in range(len(presc_line))])
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Check small strain formulation symmetry
    if strain_formulation == 1:
        if n_dim**2 == 4:
            symmetric_indexes = np.array([[2],[1]])
        elif n_dim**2 == 9:
            symmetric_indexes = np.array([[3,6,7],[1,2,5]])
        for i in range(symmetric_indexes.shape[1]):
            if mac_load_type == 1:
                isEqual = np.allclose(
                          mac_load['strain'][symmetric_indexes[0,i],1],
                          mac_load['strain'][symmetric_indexes[1,i],1],atol=1e-10)
                if not isEqual:
                    location = inspect.getframeinfo(inspect.currentframe())
                    errors.displayWarning('W00001',location.filename,location.lineno+1,
                                                                              mac_load_type)
                    mac_load['strain'][symmetric_indexes[1,i],1] = \
                                      mac_load['strain'][symmetric_indexes[0,i],1]
            elif mac_load_type == 2:
                isEqual = np.allclose(
                          mac_load['stress'][symmetric_indexes[0,i],1],
                          mac_load['stress'][symmetric_indexes[1,i],1],atol=1e-10)
                if not isEqual:
                    location = inspect.getframeinfo(inspect.currentframe())
                    errors.displayWarning('W00001',location.filename,location.lineno+1,
                                                                              mac_load_type)
                    mac_load['stress'][symmetric_indexes[1,i],1] = \
                                      mac_load['stress'][symmetric_indexes[0,i],1]
            elif mac_load_type == 3:
                if mac_load_typeidxs[symmetric_indexes[0,i]] != \
                                            mac_load_typeidxs[symmetric_indexes[1,i]]:
                    location = inspect.getframeinfo(inspect.currentframe())
                    errors.displayError('E00012',location.filename,location.lineno+1,i)
                aux = mac_load_typeidxs[symmetric_indexes[0,i]]
                key = 'strain' if aux == 0 else 'stress'
                isEqual = np.allclose(
                               mac_load[key][symmetric_indexes[0,i],1],
                               mac_load[key][symmetric_indexes[1,i],1],atol=1e-10)
                if not isEqual:
                    location = inspect.getframeinfo(inspect.currentframe())
                    errors.displayWarning('W00001',location.filename,location.lineno+1,
                                                                          mac_load_type,key)
                    mac_load[key][symmetric_indexes[1,i],1] = \
                                                     mac_load[key][symmetric_indexes[0,i],1]
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Order macroscale strain and stress tensors according to the defined problem
    # nonsymmetric component order
    if n_dim == 2:
        aux = {'11':0, '21':1, '12':2, '22':3}
    else:
        aux = {'11':0, '21':1, '31':2, '12':3, '22':4, '32':5, '13':6, '23':7, '33':8}
    mac_load_copy = copy.deepcopy(mac_load)
    mac_load_typeidxs_copy = copy.deepcopy(mac_load_typeidxs)
    for i in range(n_dim**2):
        if mac_load_type == 1:
            mac_load['strain'][i,:] = mac_load_copy['strain'][aux[comp_order_nsym[i]],:]
        elif mac_load_type == 2:
            mac_load['stress'][i,:] = mac_load_copy['stress'][aux[comp_order_nsym[i]],:]
        elif mac_load_type == 3:
            mac_load['strain'][i,:] = mac_load_copy['strain'][aux[comp_order_nsym[i]],:]
            mac_load['stress'][i,:] = mac_load_copy['stress'][aux[comp_order_nsym[i]],:]
            mac_load_typeidxs[i] = mac_load_typeidxs_copy[aux[comp_order_nsym[i]]]
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # For convenience, store the prescribed macroscale strains and stresses components as
    # the associated strings, i.e. 0 > 'strain' and 1 > 'stress', in a dictionary
    if n_dim == 2:
        aux = ['11','21','12','22']
    else:
        aux = ['11','21','31','12','22','32','13','23','33']
    mac_load_presctype = dict()
    for i in range(n_dim**2):
        if mac_load_typeidxs[i] == 0:
            mac_load_presctype[aux[i]] = 'strain'
        else:
            mac_load_presctype[aux[i]] = 'stress'
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    return mac_load, mac_load_presctype
# ------------------------------------------------------------------------------------------
# Read the number of clusters associated to each material phase, specified as
#
# Number_of_Clusters
# < phase_id > < number_of_clusters >
# < phase_id > < number_of_clusters >
#
# and store it in a dictionary as
#
#                    dictionary['phase_id'] = number_of_clusters
#
def readPhaseClustering(file,file_path,keyword,n_material_phases,material_properties):
    phase_n_clusters = dict()
    line_number = searchKeywordLine(file,keyword) + 1
    for iphase in range(n_material_phases):
        line = linecache.getline(file_path,line_number+iphase).split()
        if line[0] == '':
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayError('E00013',location.filename,location.lineno+1,keyword,\
                                                                                   iphase+1)
        elif len(line) != 2:
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayError('E00013',location.filename,location.lineno+1,keyword,\
                                                                                   iphase+1)
        elif not checkPositiveInteger(line[0]) or not checkPositiveInteger(line[1]):
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayError('E00013',location.filename,location.lineno+1,keyword,\
                                                                                   iphase+1)
        elif str(int(line[0])) not in material_properties.keys():
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayError('E00049',location.filename,location.lineno+1,keyword,\
                                                    int(line[0]),material_properties.keys())
        elif str(int(line[0])) in phase_n_clusters.keys():
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayError('E00050',location.filename,location.lineno+1,keyword,\
                                                                               int(line[0]))
        phase_n_clusters[str(int(line[0]))] = int(line[1])
    return phase_n_clusters
# ------------------------------------------------------------------------------------------
# Read the spatial discretization file absolute path
#
# Discretization_File
# < absolute_path >
#
def readDiscretizationFilePath(file,file_path,keyword,valid_exts):
    line_number = searchKeywordLine(file,keyword) + 1
    discret_file_path = linecache.getline(file_path,line_number).strip()
    if not os.path.isabs(discret_file_path):
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayError('E00014',location.filename,location.lineno+1,keyword,\
                                                                          discret_file_path)
    elif not os.path.isfile(discret_file_path):
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayError('E00014',location.filename,location.lineno+1,keyword,\
                                                                          discret_file_path)
    format_exts = ['.npy']
    if ntpath.splitext(ntpath.basename(discret_file_path))[-1] in format_exts:
        if not ntpath.splitext(ntpath.splitext(ntpath.basename(discret_file_path))[0])[-1] \
                                                                              in valid_exts:
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayError('E00015',location.filename,location.lineno+1,keyword,\
                                                                                 valid_exts)
        return discret_file_path
    else:
        if not ntpath.splitext(ntpath.basename(discret_file_path))[-1] in valid_exts:
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayError('E00015',location.filename,location.lineno+1,keyword,\
                                                                                 valid_exts)
        return discret_file_path
# ------------------------------------------------------------------------------------------
# Read the RVE dimensions specified as follows:
#
# 2D Problems:
#
# RVE_Dimensions
# < dim1_size > < dim2_size >
#
# 3D Problems:
#
# RVE_Dimensions
# < dim1_size > < dim2_size > < dim3_size >
#
# and store them in a list as
#
#               list = [ < dim1_size > , < dim2_size > [, < dim3_size >] ]
#
def readRVEDimensions(file,file_path,keyword,n_dim):
    keyword_line_number = searchKeywordLine(file,keyword)
    line = linecache.getline(file_path,keyword_line_number+1).split()
    if line == '':
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayError('E00031',location.filename,location.lineno+1,keyword)
    elif len(line) != n_dim:
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayError('E00031',location.filename,location.lineno+1,keyword)
    for i in range(n_dim):
        if not checkNumber(line[i]) or float(line[i]) <= 0:
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayError('E00031',location.filename,location.lineno+1,keyword)
    rve_dims = list()
    for i in range(n_dim):
        rve_dims.append(float(line[i]))
    return rve_dims
# ------------------------------------------------------------------------------------------
# Read the VTK output options specified as follows:
#
# VTK_Output [ < options > ]
#
# where the options are | format:          ascii (default) or binary
#                       | increments:      all (default) or every < positive_integer >
#                       | state variables: all_variables (default) or common_variables
#
def readVTKOptions(file,file_path,keyword,keyword_line_number):
    line = linecache.getline(file_path,keyword_line_number).split()
    line = [x.lower() if not checkNumber(x) else x for x in line]
    if 'binary' in line:
        vtk_format = 'binary'
    else:
        vtk_format = 'ascii'
    if 'every' in line:
        if not checkPositiveInteger(line[line.index('every') + 1]):
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayError('E00057',location.filename,location.lineno+1,keyword)
        vtk_inc_div = int(line[line.index('every') + 1])
    else:
        vtk_inc_div = 1
    if 'common_variables' in line:
        vtk_vars = 'common_variables'
    else:
        vtk_vars = 'all'
    return [vtk_format,vtk_inc_div,vtk_vars]
#
#                                                                      Consistency functions
# ==========================================================================================
# Set parameters dependent on the problem type
def setProblemTypeParameters(problem_type):
    # Set problem dimension and strain/stress components order in symmetric and nonsymmetric
    # cases
    if problem_type == 1:
        n_dim = 2
        comp_order_sym = ['11','22','12']
        comp_order_nsym = ['11','21','12','22']
    elif problem_type == 2:
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayError('E00017',location.filename,location.lineno+1,problem_type)
    elif problem_type == 3:
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayError('E00017',location.filename,location.lineno+1,problem_type)
    elif problem_type == 4:
        n_dim = 3
        comp_order_sym = ['11','22','33','12','23','13']
        comp_order_nsym = ['11','21','31','12','22','32','13','23','33']
    return [n_dim,comp_order_sym,comp_order_nsym]
