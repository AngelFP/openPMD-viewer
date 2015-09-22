"""
This file is part of the openPMD viewer.

It defines a function that can read standard parameters from an openPMD file.
"""
import os
import h5py

def read_openPMD_params( filename ):
    """
    Extract the time and some openPMD parameters from a file

    Parameter
    ---------
    filename: string
        The path to the file from which parameters should be extracted

    Returns
    -------
    A tuple with:
    - A float corresponding to the time of this iteration in SI units
    - A dictionary containing several parameters, such as the geometry, etc.
    """
    params = {}
            
    # Open the file, and do a version check
    f = h5py.File( filename, 'r')
    version = f.attrs['openPMD'].decode()
    if version[:2] != '1.':
        raise ValueError(
            "File %s is not supported: Invalid openPMD version: "
            "%s)" %( filename, version) )
    params['extension'] = f.attrs['openPMDextension']

    # Find the base path object, and extract the time
    bpath = f[ f.attrs["basePath"] ]
    t = bpath.attrs["time"] * bpath.attrs["timeUnitSI"]

    # Find out whether fields are present and extract their geometry
    meshes_path = f.attrs['meshesPath'].decode().strip('/')
    if meshes_path in bpath.keys():
        avail_fields = bpath[meshes_path].keys()
        # Pick the first field and inspect its geometry
        first_field_path = avail_fields[0]
        first_field = bpath[ os.path.join(meshes_path, first_field_path) ]
        params['geometry'] = first_field.attrs['geometry']
        if params['geometry'] == "cartesian":
            # Check if this a 2d or 3d Cartesian timeseries
            dim = len( first_field.attrs['axisLabels'] )
            if dim == 2:
                params['geometry'] = "2dcartesian"
            elif dim==3:
                params['geometry'] = "3dcartesian"
        # For each field, check whether it is vector or scalar
        # Store the information in a dictionary
        params['avail_fields'] = {}
        for field_name in avail_fields:
            field = bpath[ os.path.join(meshes_path, field_name) ]
            if is_scalar_record( field ):
                field_type='scalar'
            else:
                field_type='vector'
            params['avail_fields'][field_name] = field_type

    else :
        params['avail_fields'] = None

    # Find out whether particles are present, and if yes of which species
    particle_path = f.attrs['particlesPath'].decode().strip('/')
    if particle_path in bpath.keys():
        # Particles are present ; extract the species
        params['avail_species'] = bpath[particle_path].keys()
        # Extract the available particle quantity, from the first species
        first_species_path = params['avail_species'][0]
        first_species = bpath[ os.path.join(particle_path, first_species_path) ]
        ptcl_quantities = []
        # Go through all the particle quantities
        for quantity_name in first_species.keys():
            quantity = first_species[quantity_name]
            if is_scalar_record( quantity ):
                # Add the name of the scalar record
                ptcl_quantities.append( quantity_name )
            else:
                # Add each component of the vector record
                for coord in quantity.keys():
                    ptcl_quantities.append(os.path.join(quantity_name, coord))
        # Simplify the name of some standard openPMD quantities
        ptcl_quantities = simplify_quantities( ptcl_quantities )
        params['avail_ptcl_quantities'] = ptcl_quantities
    else :
        # Particles are absent
        params['avail_species'] = None
        params['avail_ptcl_quantities'] = None

    # Close the file and return the parameters
    f.close()
    return( t, params )

def is_scalar_record( record ):
    """
    Determine whether a record is a scalar record or a vector record

    Parameter
    ---------
    record: an h5py Dataset or an h5py Group

    Return
    ------
    A boolean indicating whether the record is scalar
    """
    scalar = False
    if 'value' in record.attrs:
        scalar=True
    elif type(record) is h5py.Dataset:
        scalar=True

    return(scalar)

def simplify_quantities( quantities ):
    """
    Replace the names of some standard quantities by shorter names

    Parameter
    ---------
    quantities: a list of strings
        A list of available particle quantities
    
    Returns
    -------
    A list with shorter names, where applicable
    """
    # Replace the names of the positions
    if ('position/x' in quantities) and ('positionOffset/x' in quantities):
        quantities.remove('position/x')
        quantities.remove('positionOffset/x')
        quantities.append('x')
    if ('position/y' in quantities) and ('positionOffset/y' in quantities):
        quantities.remove('position/y')
        quantities.remove('positionOffset/y')
        quantities.append('y')
    if ('position/z' in quantities) and ('positionOffset/z' in quantities):
        quantities.remove('position/z')
        quantities.remove('positionOffset/z')
        quantities.append('z')

    # Replace the names of the momenta
    if 'momentum/x' in quantities:
        quantities.remove('momentum/x')
        quantities.append('ux')
    if 'momentum/y' in quantities:
        quantities.remove('momentum/y')
        quantities.append('uy')
    if 'momentum/z' in quantities:                
        quantities.remove('momentum/z')
        quantities.append('uz')

    # Replace the name for 'weights'
    if 'weighting' in quantities:
        quantities.remove('weighting')
        quantities.append('w')

    # Remove some of the less interesting parameters
    if 'mass' in quantities:
        quantities.remove('mass')
    if 'charge' in quantities:
        quantities.remove('charge')

    return(quantities)
