#
# Links Interface (UNNAMED Program)
# ==========================================================================================
# Summary:
# ...
# ------------------------------------------------------------------------------------------
# Development history:
# Bernardo P. Ferreira | March 2020 | Initial coding.
# ==========================================================================================
#                                                                             Import modules
# ==========================================================================================
# Operating system related functions
import os
# Subprocess management
import subprocess
# Working with arrays
import numpy as np
# Extract information from path
import ntpath
# Read specific lines from file
import linecache
# Inspect file name and line
import inspect
# Generate efficient iterators
import itertools as it
# Display errors, warnings and built-in exceptions
import ioput.errors as errors
# Manage files and directories
import ioput.fileoperations as filop
# Matricial operations
import tensor.matrixoperations as mop
#
#                                                                    Links parameters reader
#                                                                          (input data file)
# ==========================================================================================
# Read the parameters from the input data file required to generate the Links input data
# file and solve the microscale equilibrium problem
def readLinksParameters(file,file_path,problem_type,checkNumber,checkPositiveInteger,
                                               searchKeywordLine,searchOptionalKeywordLine):
    # Initialize Links parameters dictionary
    Links_dict = dict()
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Set Links problem type
    problem_type_converter = {'1':2, '2':1, '3':3, '4':6}
    Links_dict['analysis_type'] = problem_type_converter[str(problem_type)]
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read the Links binary absolute path
    keyword = 'Links_bin'
    line_number = searchKeywordLine(file,keyword) + 1
    Links_bin_path = linecache.getline(file_path,line_number).strip()
    if not os.path.isabs(Links_bin_path):
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayerror('E00068',location.filename,location.lineno+1,keyword, \
                                                                             Links_bin_path)
    elif not os.path.isfile(Links_bin_path):
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayerror('E00068',location.filename,location.lineno+1,keyword, \
                                                                             Links_bin_path)
    # Store Links binary absolute path
    Links_dict['Links_bin_path'] = Links_bin_path
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read the finite element order (linear or quadratic). If the associated keyword is not
    # found, then a default specification is assumed
    keyword = 'Links_FE_order'
    isFound,keyword_line_number = searchOptionalKeywordLine(file,keyword)
    if isFound:
        line = linecache.getline(file_path,keyword_line_number).split()
        if len(line) == 1:
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayerror('E00063',location.filename,location.lineno+1,keyword)
        elif line[1] not in ['linear','quadratic']:
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayerror('E00063',location.filename,location.lineno+1,keyword)
        fe_order = line[1]
    else:
        fe_order = 'quadratic'
    # Store finite element order
    Links_dict['fe_order'] = fe_order
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read microscale boundary condition. If the associated keyword is not found, then a
    # default specification is assumed
    keyword = 'Links_boundary_type'
    isFound,keyword_line_number = searchOptionalKeywordLine(file,keyword)
    if isFound:
        line = linecache.getline(file_path,keyword_line_number).split()
        if len(line) == 1:
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayerror('E00064',location.filename,location.lineno+1,keyword)
        elif line[1] not in ['Taylor_Condition','Linear_Condition','Periodic_Condition',
                               'Uniform_Traction_Condition','Uniform_Traction_Condition_II',
                                'Mortar_Periodic_Condition','Mortar_Periodic_Condition_LM']:
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayerror('E00064',location.filename,location.lineno+1,keyword)
        boundary_type = line[1]
    else:
        boundary_type = 'Periodic_Condition'
    # Store microscale boundary condition
    Links_dict['boundary_type'] = boundary_type
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read convergence tolerance. If the associated keyword is not found, then a default
    # specification is assumed
    keyword = 'Links_convergence_tolerance'
    isFound,keyword_line_number = searchOptionalKeywordLine(file,keyword)
    if isFound:
        line = linecache.getline(file_path,keyword_line_number+1).split()
        if line == '':
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayerror('E00065',location.filename,location.lineno+1,keyword)
        elif len(line) != 1:
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayerror('E00065',location.filename,location.lineno+1,keyword)
        elif not checkNumber(line[0]) or float(line[0]) <= 0:
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayerror('E00065',location.filename,location.lineno+1,keyword)
        convergence_tolerance = float(line[0])
    else:
        convergence_tolerance = 1e-6
    # Store convergence tolerance
    Links_dict['convergence_tolerance'] = convergence_tolerance
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Read elemental average output mode. If the associated keyword is not found, then a
    # default specification is assumed
    keyword = 'Links_Element_Average_Output_Mode'
    isFound,keyword_line_number = searchOptionalKeywordLine(file,keyword)
    if isFound:
        if len(line) == 1:
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayerror('E00069',location.filename,location.lineno+1,keyword)
        elif not checkPositiveInteger(line[1]):
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayerror('E00069',location.filename,location.lineno+1,keyword)
        element_avg_output_mode = int(line[1])
    else:
        element_avg_output_mode = 1
    # Store element average output mode
    Links_dict['element_avg_output_mode'] = element_avg_output_mode
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    return Links_dict
#
#                                                           Links input data file generation
# ==========================================================================================
# Write Links input data file for a given macroscale strain loading
def writeLinksInputDataFile(file_name,dirs_dict,problem_dict,mat_dict,rg_dict,clst_dict,
                                                                                mac_strain):
    # Get directories data
    offline_stage_dir = dirs_dict['offline_stage_dir']
    # Get problem data
    n_dim = problem_dict['n_dim']
    # Get material data
    n_material_phases = mat_dict['n_material_phases']
    material_phases = mat_dict['material_phases']
    material_properties = mat_dict['material_properties']
    material_phases_models = mat_dict['material_phases_models']
    # Get regular grid data
    n_voxels_dims = rg_dict['n_voxels_dims']
    rve_dims = rg_dict['rve_dims']
    regular_grid = rg_dict['regular_grid']
    rg_file_name = rg_dict['rg_file_name']
    # Get Links input data file parameters
    Links_dict = clst_dict['Links_dict']
    fe_order = Links_dict['fe_order']
    analysis_type = Links_dict['analysis_type']
    boundary_type = Links_dict['boundary_type']
    convergence_tolerance = Links_dict['convergence_tolerance']
    element_avg_output_mode = Links_dict['element_avg_output_mode']
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Set and create offline stage Links directory if it does not exist
    os_Links_dir = offline_stage_dir + 'Links' + '/'
    if not os.path.exists(os_Links_dir):
        filop.makedirectory(os_Links_dir)
    # Set Links input data file path
    Links_file_path = os_Links_dir + file_name + '.rve'
    # Abort if attempting to overwrite an existing Links input data file
    if os.path.isfile(Links_file_path):
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayerror('E00066',location.filename,location.lineno+1,
                                                           ntpath.basename(Links_file_path))
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Set additional Links input data file parameters (fixed)
    title = 'Links input data file generated automatically by UNNAMED program'
    large_strain_formulation = 'OFF'
    number_of_increments = 1
    solver = 'PARDISO'
    parallel_solver = 4
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Generate Links finite element mesh
    coords,connectivities,element_phases = generateFEMesh(n_dim,rve_dims,n_voxels_dims,
                                                                      regular_grid,fe_order)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Open Links input data file
    Links_file = open(Links_file_path,'w')
    # Format file structure
    write_list = ['\n' + 'TITLE ' + '\n' + title + '\n'] + \
                 ['\n' + 'ANALYSIS_TYPE ' + str(analysis_type) + '\n'] + \
                 ['\n' + 'LARGE_STRAIN_FORMULATION ' + large_strain_formulation + '\n'] + \
                 ['\n' + 'Boundary_Type ' + boundary_type + '\n'] + \
                 ['\n' + 'Prescribed_Epsilon' + '\n'] + \
                 [' '.join([str('{:16.8e}'.format(mac_strain[i,j]))
                          for j in range(n_dim)]) + '\n' for i in range(n_dim)] + ['\n'] + \
                 ['Number_of_Increments ' + str(number_of_increments) + '\n'] + \
                 ['\n' + 'CONVERGENCE_TOLERANCE' + '\n' + str(convergence_tolerance) +
                                                                                   '\n'] + \
                 ['\n' + 'SOLVER ' + solver + '\n'] + \
                 ['\n' + 'PARALLEL_SOLVER ' + str(parallel_solver) + '\n'] + \
                 ['\n' + 'VTK_OUTPUT' + '\n'] + \
                 ['\n' + 'Element_Average_Output ' + str(element_avg_output_mode) + '\n']
    # Write Links input data file
    Links_file.writelines(write_list)
    # Close Links input data file
    Links_file.close()
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Append finite element mesh to Links input data file
    writeLinksFEMesh(Links_file_path,n_dim,n_material_phases,material_phases,
                  material_properties,material_phases_models,fe_order,coords,connectivities,
                                                                             element_phases)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Create a file containing solely the Links finite element mesh data if it does not
    # exist yet
    mesh_path = os_Links_dir + rg_file_name + '.femsh'
    if not os.path.isfile(mesh_path):
        writeLinksFEMesh(mesh_path,n_dim,n_material_phases,material_phases,
                                 material_properties,material_phases_models,fe_order,coords,
                                                              connectivities,element_phases)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Return
    return Links_file_path
#
#                                                                  Links finite element mesh
# ==========================================================================================
# Generate regular mesh of quadrilateral (2D) / hexahedral (3D) finite linear or quadratic
# elements
def generateFEMesh(n_dim,rve_dims,n_voxels_dims,regular_grid,fe_order):
    # Initialize array with finite element mesh nodes
    if fe_order == 'linear':
        nodes_grid = np.zeros(np.array(n_voxels_dims)+1,dtype=int)
    else:
        nodes_grid = np.zeros(2*np.array(n_voxels_dims)+1,dtype=int)
    # Initialize coordinates dictionary
    coords = dict()
    # Initialize connectivities dictionary
    connectivities = dict()
    # Initialize element phases dictionary
    element_phases = dict()
    # Set sampling periods in each dimension
    sampling_period = [rve_dims[i]/n_voxels_dims[i] for i in range(n_dim)]
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Set nodes coordinates
    node = 1
    if n_dim == 2:
        # Set nodes for linear (QUAD4) or quadratic (QUAD8) finite element mesh
        if fe_order == 'linear':
            # Loop over nodes
            for j in range(n_voxels_dims[1]+1):
                for i in range(n_voxels_dims[0]+1):
                    nodes_grid[i,j] = node
                    # Set node coordinates
                    coords[str(node)] = [i*sampling_period[0],j*sampling_period[1]]
                    # Increment node counter
                    node = node + 1
        elif fe_order == 'quadratic':
            # Loop over nodes
            for j in range(2*n_voxels_dims[1]+1):
                for i in range(2*n_voxels_dims[0]+1):
                    if j % 2 != 0 and i % 2 != 0:
                        # Skip inexistent node
                        nodes_grid[i,j] = -1
                    else:
                        nodes_grid[i,j] = node
                        # Set node coordinates
                        coords[str(node)] = \
                                         [i*0.5*sampling_period[0],j*0.5*sampling_period[1]]
                        # Increment node counter
                        node = node + 1
    elif n_dim == 3:
        # Set nodes for linear (HEXA8) or quadratic (HEXA20) finite element mesh
        if fe_order == 'linear':
            # Loop over nodes
            for k in range(n_voxels_dims[2]+1):
                for j in range(n_voxels_dims[1]+1):
                    for i in range(n_voxels_dims[0]+1):
                        nodes_grid[i,j,k] = node
                        # Set node coordinates
                        coords[str(node)] = \
                            [i*sampling_period[0],j*sampling_period[1],k*sampling_period[2]]
                        # Increment node counter
                        node = node + 1
        if fe_order == 'quadratic':
            # Loop over nodes
            for k in range(2*n_voxels_dims[2]+1):
                for j in range(2*n_voxels_dims[1]+1):
                    for i in range(2*n_voxels_dims[0]+1):
                        # Skip inexistent node
                        if (j % 2 != 0 and i % 2 != 0) or \
                                                (k % 2 != 0 and (j % 2 != 0 or i % 2 != 0)):
                            nodes_grid[i,j,k] = -1
                        else:
                            # Set node coordinates
                            nodes_grid[i,j,k] = node
                            coords[str(node)] = [i*0.5*sampling_period[0], \
                                          j*0.5*sampling_period[1],k*0.5*sampling_period[2]]
                            # Increment node counter
                            node = node + 1
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Set element connectivities and material phases
    elem = 1
    if n_dim == 2:
        # Set linear (QUAD4) or quadratic (QUAD8) finite element mesh connectivities
        if fe_order == 'linear':
            # Loop over elements
            for j in range(n_voxels_dims[1]):
                for i in range(n_voxels_dims[0]):
                    # Set element connectivities
                    connectivities[str(elem)] = [nodes_grid[i,j],nodes_grid[i+1,j],
                                                      nodes_grid[i+1,j+1],nodes_grid[i,j+1]]
                    # Set element material phase
                    element_phases[str(elem)] = regular_grid[i,j]
                    # Increment element counter
                    elem = elem + 1
        elif fe_order == 'quadratic':
            # Loop over elements
            for j in range(n_voxels_dims[1]):
                for i in range(n_voxels_dims[0]):
                    # Set element connectivities
                    connectivities[str(elem)] = [nodes_grid[2*i,2*j],nodes_grid[2*i+1,2*j],
                                              nodes_grid[2*i+2,2*j],nodes_grid[2*i+2,2*j+1],
                                           nodes_grid[2*i+2,2*j+2], nodes_grid[2*i+1,2*j+2],
                                                nodes_grid[2*i,2*j+2],nodes_grid[2*i,2*j+1]]
                    # Set element material phase
                    element_phases[str(elem)] = regular_grid[i,j]
                    # Increment element counter
                    elem = elem + 1
    elif n_dim == 3:
        # Set linear (HEXA8) or quadratic (HEXA20) finite element mesh connectivities
        if fe_order == 'linear':
            # Loop over elements
            for k in range(n_voxels_dims[2]):
                for j in range(n_voxels_dims[1]):
                    for i in range(n_voxels_dims[0]):
                        # Set element connectivities
                        connectivities[str(elem)] = [nodes_grid[i,j,k],nodes_grid[i,j,k+1],
                                                  nodes_grid[i+1,j,k+1],nodes_grid[i+1,j,k],
                                                  nodes_grid[i,j+1,k],nodes_grid[i,j+1,k+1],
                                              nodes_grid[i+1,j+1,k+1],nodes_grid[i+1,j+1,k]]
                        # Set element material phase
                        element_phases[str(elem)] = regular_grid[i,j,k]
                        # Increment element counter
                        elem = elem + 1
        elif fe_order == 'quadratic':
            # Loop over elements
            for k in range(n_voxels_dims[2]):
                for j in range(n_voxels_dims[1]):
                    for i in range(n_voxels_dims[0]):
                        # Set element connectivities
                        connectivities[str(elem)] = [nodes_grid[2*i,2*j,2*k],
                                      nodes_grid[2*i,2*j,2*k+2],nodes_grid[2*i+2,2*j,2*k+2],
                                        nodes_grid[2*i+2,2*j,2*k],nodes_grid[2*i,2*j+2,2*k],
                                  nodes_grid[2*i,2*j+2,2*k+2],nodes_grid[2*i+2,2*j+2,2*k+2],
                                      nodes_grid[2*i+2,2*j+2,2*k],nodes_grid[2*i,2*j,2*k+1],
                                    nodes_grid[2*i+1,2*j,2*k+2],nodes_grid[2*i+2,2*j,2*k+1],
                                        nodes_grid[2*i+1,2*j,2*k],nodes_grid[2*i,2*j+1,2*k],
                                  nodes_grid[2*i,2*j+1,2*k+2],nodes_grid[2*i+2,2*j+1,2*k+2],
                                    nodes_grid[2*i+2,2*j+1,2*k],nodes_grid[2*i,2*j+2,2*k+1],
                                nodes_grid[2*i+1,2*j+2,2*k+2],nodes_grid[2*i+2,2*j+2,2*k+1],
                                                                nodes_grid[2*i+1,2*j+2,2*k]]
                        # Set element material phase
                        element_phases[str(elem)] = regular_grid[i,j,k]
                        # Increment element counter
                        elem = elem + 1
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Return
    return [coords,connectivities,element_phases]
# ------------------------------------------------------------------------------------------
# Append Links finite element mesh (groups, elements, materials, element connectivities and
# nodal coordinates) to a given data file
def writeLinksFEMesh(file_path,n_dim,n_material_phases,material_phases,material_properties,
                      material_phases_models,fe_order,coords,connectivities,element_phases):
    # Set element designation and number of Gauss integration points
    if n_dim == 2:
        if fe_order == 'linear':
            elem_type = 'QUAD4'
            n_gp = 4
        else:
            elem_type = 'QUAD8'
            n_gp = 4
    else:
        if fe_order == 'linear':
            elem_type = 'HEXA8'
            n_gp = 8
        else:
            elem_type = 'HEXA20'
            n_gp = 8
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Open data file to append Links finite element mesh
    data_file = open(file_path,'a')
    # Format file structure
    write_list = ['\n' + 'ELEMENT_GROUPS ' + str(n_material_phases) + '\n'] + \
                 [str(mat+1) + ' 1 ' + str(mat+1) + '\n' \
                                                    for mat in range(n_material_phases)] + \
                 ['\n' + 'ELEMENT_TYPES 1' + '\n', '1 ' + elem_type + '\n', '  ' + \
                                                               str(n_gp) + ' GP' + '\n'] + \
                 ['\n' + 'MATERIALS ' + str(n_material_phases) + '\n']
    # Append first part of the Links finite element mesh to data file
    data_file.writelines(write_list)
    # Close data file
    data_file.close()
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Append material phases Links constitutive models and associated properties
    for mat_phase in material_phases:
        material_phases_models[mat_phase]['writeMaterialProperties'](file_path,
                                                   mat_phase,material_properties[mat_phase])
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Open data file to append Links finite element mesh
    data_file = open(file_path,'a')
    # Format file structure
    write_list = ['\n' + 'ELEMENTS ' + str(len(connectivities.keys())) + '\n'] + \
                 ['{:>3s}'.format(str(elem)) + \
                          '{:^5d}'.format(element_phases[str(elem)]) + ' '.join([str(node) \
                                            for node in connectivities[str(elem)]]) + '\n' \
                       for elem in np.sort([int(key) for key in connectivities.keys()])] + \
                 ['\n' + 'NODE_COORDINATES ' + str(len(coords.keys())) + \
                                                                    ' CARTESIAN' + '\n'] + \
                 ['{:>3s}'.format(str(node)) + ' ' + \
                                                   ' '.join([str('{:16.8e}'.format(coord)) \
                                                   for coord in coords[str(node)]]) + '\n' \
                                   for node in np.sort([int(key) for key in coords.keys()])]
    # Append last part of the Links finite element mesh to data file
    data_file.writelines(write_list)
    # Close data file
    data_file.close()
#
#                                                         Links material constitutive models
# ==========================================================================================
# Set material procedures for a given Links constitutive model
def LinksMaterialProcedures(model_name):
    if model_name == 'ELASTIC':
        # Set the constitutive model required material properties
        def setRequiredProperties():
            # Set required material properties
            req_material_properties = ['density','E','v']
            # Return
            return req_material_properties
        # ----------------------------------------------------------------------------------
        # Append Links constitutive model properties specification to a given data file
        def writeMaterialProperties(file_path,mat_phase,properties):
            # Open data file to append Links constitutive model properties
            data_file = open(file_path,'a')
            # Format file structure
            write_list = [mat_phase + ' ' + 'ELASTIC' + '\n'] + \
                         [(len(mat_phase) + 1)*' ' + \
                                   str('{:16.8e}'.format(properties['density'])) + '\n'] + \
                         [(len(mat_phase) + 1)*' ' + \
                                             str('{:16.8e}'.format(properties['E'])) +
                                             str('{:16.8e}'.format(properties['v'])) + '\n']
            # Append Links constitutive model properties
            data_file.writelines(write_list)
            # Close data file
            data_file.close()
        # ----------------------------------------------------------------------------------
        # Build Links constitutive model required integer and real material properties
        # arrays (must be compatible with Links rdXXXX.f90)
        def linksXPROPS(properties):
            # Get material properties
            density = properties['density']
            E = properties['E']
            v = properties['v']
            # Compute shear and bulk modulii
            G = E/(2.0*(1.0 + v))
            K = E/(3.0*(1.0 - 2.0*v))
            # Set material type and material class
            mat_type = 1
            mat_class = 1
            # Build Links IPROPS and RPROPS arrays
            IPROPS = np.zeros(2,dtype = np.int32)
            IPROPS[0] = mat_type
            IPROPS[1] = mat_class
            RPROPS = np.zeros(3,dtype = float)
            RPROPS[0] = density
            RPROPS[1] = G
            RPROPS[2] = K
            # Return
            return [IPROPS,RPROPS]
        # ----------------------------------------------------------------------------------
        # Set Links constitutive model Gauss point variables arrays (must be compatible
        # with material_mod.f90) or get the state variables from the associated Links arrays
        def linksXXXXVA(mode,problem_dict,*args):
            # Get problem parameters
            problem_type = problem_dict['problem_type']
            n_dim = problem_dict['n_dim']
            comp_order = problem_dict['comp_order_sym']
            # Get Links parameters
            Links_comp_order,_ = getLinksCompOrder(n_dim)
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # Set Links constitutive model Gauss point variables arrays
            if mode == 'set':
                # Unpack input arguments
                state_variables = args[0]
                # Set Links strain and stress dimensions
                if problem_type == 1:
                    NSTRE = 4
                    NSTRA = 4
                else:
                    NSTRE = 6
                    NSTRA = 6
                # Get Cauchy stress
                stress_mf = state_variables['stress_mf']
                # Get real state variables
                e_strain_mf = state_variables['e_strain_mf']
                # Set logical algorithmic variables
                is_su_fail = False
                is_plast = False
                # Set Links STRES, RSTAVA, LALGVA and RALGVA arrays
                i_end = len(comp_order)
                STRES = np.zeros(NSTRE)
                STRES[0:i_end] = setTensorMatricialFormLinks(mop.gettensorfrommf(
                            stress_mf,n_dim,comp_order),n_dim,Links_comp_order,'stress')
                RSTAVA = np.zeros(NSTRA)
                RSTAVA[0:i_end] = \
                                 setTensorMatricialFormLinks(mop.gettensorfrommf(
                              e_strain_mf,n_dim,comp_order),n_dim,Links_comp_order,'strain')
                LALGVA = np.zeros(2,dtype = np.int32)
                LALGVA[0] = int(is_su_fail)
                LALGVA[1] = int(is_plast)
                RALGVA = np.zeros(1,dtype = float)
                # Return
                return [STRES,RSTAVA,LALGVA,RALGVA]
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # Get state variables from the associated Links arrays
            elif mode == 'get':
                # Unpack input arguments
                properties = args[0]
                STRES = args[1]
                RSTAVA = args[2]
                LALGVA = args[3]
                RALGVA = args[4]
                # Initialize state variables dictionary
                state_variables = init(problem_dict)
                # Get state variables
                i_end = len(comp_order)
                state_variables['e_strain_mf'] = \
                             mop.gettensormf(getTensorFromMatricialFormLinks(
                          RSTAVA[0:i_end],n_dim,Links_comp_order,'strain'),n_dim,comp_order)
                state_variables['strain_mf'] = \
                             mop.gettensormf(getTensorFromMatricialFormLinks(
                          RSTAVA[0:i_end],n_dim,Links_comp_order,'strain'),n_dim,comp_order)
                state_variables['stress_mf'] = \
                             mop.gettensormf(getTensorFromMatricialFormLinks(
                           STRES[0:i_end],n_dim,Links_comp_order,'strain'),n_dim,comp_order)
                state_variables['is_su_fail'] = bool(LALGVA[0])
                # Compute out-of-plane stress component in a 2D plane strain problem
                # (output purpose only)
                if problem_type == 1:
                    # Get material properties
                    E = properties['E']
                    v = properties['v']
                    # Compute Lamé parameters
                    lam = (E*v)/((1.0+v)*(1.0-2.0*v))
                    # Compute out-of-plane stress component
                    e_strain_mf = state_variables['e_strain_mf']
                    stress_33 = lam*(e_strain_mf[comp_order.index('11')] + \
                                                        e_strain_mf[comp_order.index('22')])
                    state_variables['stress_33'] = stress_33
                # Return
                return state_variables
        # ----------------------------------------------------------------------------------
        # Define material constitutive model state variables and build an initialized state
        # variables dictionary
        def init(problem_dict):
            # Get problem data
            n_dim = problem_dict['n_dim']
            comp_order = problem_dict['comp_order_sym']
            problem_type = problem_dict['problem_type']
            # Define constitutive model state variables (names and initialization)
            state_variables_init = dict()
            state_variables_init['e_strain_mf'] = \
                        mop.gettensormf(np.zeros((n_dim,n_dim)),n_dim,comp_order)
            state_variables_init['strain_mf'] = \
                        mop.gettensormf(np.zeros((n_dim,n_dim)),n_dim,comp_order)
            state_variables_init['stress_mf'] = \
                        mop.gettensormf(np.zeros((n_dim,n_dim)),n_dim,comp_order)
            state_variables_init['is_su_fail'] = False
            # Set additional out-of-plane stress component in a 2D plane strain problem
            # (output purpose only)
            if problem_type == 1:
                state_variables_init['stress_33'] = 0.0
            # Return initialized state variables dictionary
            return state_variables_init
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Return
    return [setRequiredProperties,writeMaterialProperties,linksXPROPS,linksXXXXVA,init]
#
#                                                                         Links program call
# ==========================================================================================
# Solve a given microscale equilibrium problem with program Links
def runLinks(Links_bin_path,Links_file_path):
    # Call program Links
    subprocess.run([Links_bin_path,Links_file_path],stdout=subprocess.PIPE,\
                                                                     stderr=subprocess.PIPE)
    # Check if the microscale equilibrium problem was successfully solved
    screen_file_name = ntpath.splitext(ntpath.basename(Links_file_path))[0]
    screen_file_path = ntpath.dirname(Links_file_path) + '/' + \
                                       screen_file_name + '/' + screen_file_name + '.screen'
    if not os.path.isfile(screen_file_path):
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayerror('E00071',location.filename,location.lineno+1,screen_file_path)
    else:
        is_solved = False
        screen_file = open(screen_file_path,'r')
        screen_file.seek(0)
        line_number = 0
        for line in screen_file:
            line_number = line_number + 1
            if 'Program L I N K S successfully completed.' in line:
                is_solved = True
                break
        if not is_solved:
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayerror('E00072',location.filename,location.lineno+1,
                                                           ntpath.basename(Links_file_path))
#
#                                                                 Post process Links results
# ==========================================================================================
# Get the elementwise average strain tensor components
def getStrainVox(Links_file_path,n_dim,comp_order,n_voxels_dims):
    # Initialize strain tensor
    strain_vox = {comp: np.zeros(tuple(n_voxels_dims)) for comp in comp_order}
    # Set elementwise average output file path and check file existence
    elagv_file_name = ntpath.splitext(ntpath.basename(Links_file_path))[0]
    elagv_file_path = ntpath.dirname(Links_file_path) + '/' + \
                                          elagv_file_name + '/' + elagv_file_name + '.elavg'
    if not os.path.isfile(elagv_file_path):
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayerror('E00070',location.filename,location.lineno+1,elagv_file_path)
    # Load elementwise average strain tensor components
    elagv_array = np.genfromtxt(elagv_file_path,autostrip=True)
    # Get Links strain components order
    Links_comp_order_sym,_ = getLinksCompOrder(n_dim)
    # Loop over Links strain components
    for i in range(len(Links_comp_order_sym)):
        # Get Links strain component
        Links_comp = Links_comp_order_sym[i]
        # Set Links Voigt notation factor
        Voigt_factor = 2.0 if Links_comp[0] != Links_comp[1] else 1.0
        # Store elementwise average strain component
        strain_vox[Links_comp] = \
                        (1.0/Voigt_factor)*elagv_array[i,:].reshape(n_voxels_dims,order='F')
    # Return
    return strain_vox
# ------------------------------------------------------------------------------------------
# Set Links strain/stress components order in symmetric and nonsymmetric cases
def getLinksCompOrder(n_dim):
    if n_dim == 2:
        Links_comp_order_sym = ['11','22','12']
        Links_comp_order_nsym = ['11','21','12','22']
    else:
        Links_comp_order_sym = ['11','22','33','12','23','13']
        Links_comp_order_nsym = ['11','21','31','12','22','32','13','23','33']
    return [Links_comp_order_sym,Links_comp_order_nsym]
#
#                                                         Links Tensorial < > Matricial Form
# ==========================================================================================
# Store a given second-order or fourth-order tensor in matricial form for a given number of
# dimensions and given ordered component list. If the second-order tensor is symmetric or
# the fourth-order tensor has minor symmetry (component list only contains independent
# components), then the Voigt notation is employed to perform the storage. The tensor
# recovery from the associated matricial form follows an precisely inverse procedure.
#
# Note: The Voigt notation depends on the nature of the tensor. For tensor natures are
#       covered in this function, namely: 'strain'/'stress' associated to a given
#       second-order tensor; 'elasticity'/'compliance' associated to a given fourth-order
#       tensor. If the symmetries are to be ignored, then the provided nature specification
#       is ignored as well.
#
# Note: The storage in matricial form is done and assumed to be provided columnwise.
#
def setTensorMatricialFormLinks(tensor,n_dim,comp_order,nature):
    # Set tensor order
    tensor_order = len(tensor.shape)
    # Check input arguments validity
    if tensor_order not in [2,4]:
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayerror('E00023',location.filename,location.lineno+1)
    elif any([ int(x) not in range(1,n_dim+1) for x in list(''.join(comp_order))]):
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayerror('E00024',location.filename,location.lineno+1)
    elif any([tensor.shape[i] != n_dim for i in range(len(tensor.shape))]):
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayerror('E00025',location.filename,location.lineno+1)
    elif any([len(comp) != 2 for comp in comp_order]):
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayerror('E00024',location.filename,location.lineno+1)
    elif len(list(dict.fromkeys(comp_order))) != len(comp_order):
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayerror('E00026',location.filename,location.lineno+1)
    # Set Voigt notation flag
    if len(comp_order) == n_dim**2:
        isVoigtNotation = False
    elif len(comp_order) == sum(range(n_dim+1)):
        if nature not in ['strain','stress','elasticity','compliance']:
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayerror('E00083',location.filename,location.lineno+1)
        isVoigtNotation = True
    else:
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayerror('E00027',location.filename,location.lineno+1)
    # Store tensor according to tensor order
    if tensor_order == 2:
        # Set second-order and matricial form indexes
        so_indexes = list()
        mf_indexes = list()
        for i in range(len(comp_order)):
            so_indexes.append([int(x)-1 for x in list(comp_order[i])])
            mf_indexes.append( comp_order.index(comp_order[i]))
        # Initialize tensor matricial form
        if tensor.dtype == 'complex':
            tensor_mf = np.zeros(len(comp_order),dtype=complex)
        else:
            tensor_mf = np.zeros(len(comp_order))
        # Store tensor in matricial form
        for i in range(len(mf_indexes)):
            mf_idx = mf_indexes[i]
            so_idx = tuple(so_indexes[i])
            factor = 1.0
            if isVoigtNotation and not so_idx[0] == so_idx[1]:
                factor = 2.0
            tensor_mf[mf_idx] = factor*tensor[so_idx]
    elif tensor_order == 4:
        # Set cartesian product of component list
        comps = list(it.product(comp_order,comp_order))
        # Set fourth-order and matricial form indexes
        fo_indexes = list()
        mf_indexes = list()
        for i in range(len(comp_order)**2):
            fo_indexes.append([int(x)-1 for x in list(comps[i][0]+comps[i][1])])
            mf_indexes.append([x for x in \
                             [comp_order.index(comps[i][0]),comp_order.index(comps[i][1])]])
        # Initialize tensor matricial form
        if tensor.dtype == 'complex':
            tensor_mf = np.zeros((len(comp_order),len(comp_order)),dtype=complex)
        else:
            tensor_mf = np.zeros((len(comp_order),len(comp_order)))
        # Store tensor in matricial form
        for i in range(len(mf_indexes)):
            mf_idx = tuple(mf_indexes[i])
            fo_idx = tuple(fo_indexes[i])
            factor = 1.0
            if isVoigtNotation and not (fo_idx[0] == fo_idx[1] and fo_idx[2] == fo_idx[3]):
                factor = factor*2.0 if fo_idx[0] != fo_idx[1] else factor
                factor = factor*2.0 if fo_idx[2] != fo_idx[3] else factor
            tensor_mf[mf_idx] = factor*tensor[fo_idx]
    # Return
    return tensor_mf
# ------------------------------------------------------------------------------------------
def getTensorFromMatricialFormLinks(tensor_mf,n_dim,comp_order,nature):
    # Set tensor order
    if len(tensor_mf.shape) == 1:
        tensor_order = 2
        if tensor_mf.shape[0] != n_dim**2 and tensor_mf.shape[0] != sum(range(n_dim+1)):
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayerror('E00028',location.filename,location.lineno+1)
    elif len(tensor_mf.shape) == 2:
        tensor_order = 4
        if tensor_mf.shape[0] != tensor_mf.shape[1]:
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayerror('E00029',location.filename,location.lineno+1)
        elif tensor_mf.shape[0] != n_dim**2 and tensor_mf.shape[0] != sum(range(n_dim+1)):
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayerror('E00028',location.filename,location.lineno+1)
    else:
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayerror('E00030',location.filename,location.lineno+1)
    # Check input arguments validity
    if any([ int(x) not in range(1,n_dim+1) for x in list(''.join(comp_order))]):
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayerror('E00024',location.filename,location.lineno+1)
    elif any([len(comp) != 2 for comp in comp_order]):
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayerror('E00024',location.filename,location.lineno+1)
    elif len(list(dict.fromkeys(comp_order))) != len(comp_order):
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayerror('E00026',location.filename,location.lineno+1)
    # Set Voigt notation flag
    if len(comp_order) == n_dim**2:
        isVoigtNotation = False
    elif len(comp_order) == sum(range(n_dim+1)):
        if nature not in ['strain','stress','elasticity','compliance']:
            location = inspect.getframeinfo(inspect.currentframe())
            errors.displayerror('E00083',location.filename,location.lineno+1)
        isVoigtNotation = True
    else:
        location = inspect.getframeinfo(inspect.currentframe())
        errors.displayerror('E00027',location.filename,location.lineno+1)
    # Get tensor according to tensor order
    if tensor_order == 2:
        # Set second-order and matricial form indexes
        so_indexes = list()
        mf_indexes = list()
        for i in range(len(comp_order)):
            so_indexes.append([int(x)-1 for x in list(comp_order[i])])
            mf_indexes.append( comp_order.index(comp_order[i]))
        # Initialize tensor
        if tensor_mf.dtype == 'complex':
            tensor = np.zeros(tensor_order*(n_dim ,),dtype=complex)
        else:
            tensor = np.zeros(tensor_order*(n_dim ,))
        # Get tensor from matricial form
        for i in range(len(mf_indexes)):
            mf_idx = mf_indexes[i]
            so_idx = tuple(so_indexes[i])
            factor = 1.0
            if isVoigtNotation and not so_idx[0] == so_idx[1]:
                factor = 2.0
                tensor[so_idx[::-1]] = (1.0/factor)*tensor_mf[mf_idx]
            tensor[so_idx] = (1.0/factor)*tensor_mf[mf_idx]
    elif tensor_order == 4:
        # Set cartesian product of component list
        comps = list(it.product(comp_order,comp_order))
        # Set fourth-order and matricial form indexes
        mf_indexes = list()
        fo_indexes = list()
        for i in range(len(comp_order)**2):
            fo_indexes.append([int(x)-1 for x in list(comps[i][0]+comps[i][1])])
            mf_indexes.append([x for x in \
                             [comp_order.index(comps[i][0]),comp_order.index(comps[i][1])]])
        # Initialize tensor
        if tensor_mf.dtype == 'complex':
            tensor = np.zeros(tensor_order*(n_dim ,),dtype=complex)
        else:
            tensor = np.zeros(tensor_order*(n_dim ,))
        # Get tensor from matricial form
        for i in range(len(mf_indexes)):
            mf_idx = tuple(mf_indexes[i])
            fo_idx = tuple(fo_indexes[i])
            factor = 1.0
            if isVoigtNotation and not (fo_idx[0] == fo_idx[1] and fo_idx[2] == fo_idx[3]):
                factor = factor*2.0 if fo_idx[0] != fo_idx[1] else factor
                factor = factor*2.0 if fo_idx[2] != fo_idx[3] else factor
                if fo_idx[0] != fo_idx[1] and fo_idx[2] != fo_idx[3]:
                    tensor[tuple(fo_idx[1::-1]+fo_idx[2:])] = (1.0/factor)*tensor_mf[mf_idx]
                    tensor[tuple(fo_idx[:2]+fo_idx[3:1:-1])] = \
                                                              (1.0/factor)*tensor_mf[mf_idx]
                    tensor[tuple(fo_idx[1::-1]+fo_idx[3:1:-1])] = \
                                                              (1.0/factor)*tensor_mf[mf_idx]
                elif fo_idx[0] != fo_idx[1]:
                    tensor[tuple(fo_idx[1::-1]+fo_idx[2:])] = (1.0/factor)*tensor_mf[mf_idx]
                elif fo_idx[2] != fo_idx[3]:
                    tensor[tuple(fo_idx[:2]+fo_idx[3:1:-1])] = \
                                                              (1.0/factor)*tensor_mf[mf_idx]
            tensor[fo_idx] = (1.0/factor)*tensor_mf[mf_idx]
    # Return
    return tensor
