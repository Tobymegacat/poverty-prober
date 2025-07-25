import h5py
import numpy as np
from typing import List, Tuple, Optional

class WaferHDF5Manager:
    """
    Manager class for initializing and working with HDF5 files for wafer chip measurements.
    
    Structure:
    wafer_name/
    ├── dies/
    │   ├── die_001/
    │   │   ├── location (x, y coordinates on wafer)
    │   │   ├── gds_file (string)
    │   │   ├── die_id (integer)
    │   │   └── junctions/
    │   │       ├── junction_001/
    │   │       │   ├── position (x, y relative to die center)
    │   │       │   ├── resistance_values (3 values)
    │   │       │   └── type (string)
    │   │       └── ...
    │   └── ...
    """
    
    def __init__(self, filename: str):
        self.filename = filename
        self.file = None
    
    def __enter__(self):
        self.file = h5py.File(self.filename, 'w')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()
    
    def initialize_wafer(self, wafer_name: str) -> h5py.Group:
        """Initialize the top-level wafer group."""
        wafer_group = self.file.create_group(wafer_name)        
        # Create dies container group
        
        dies_group = wafer_group.create_group('dies')
        
        return wafer_group
    
    def add_die(self, wafer_group: h5py.Group, die_name: str, 
                location: Tuple[float, float], gds_file: str, die_id: int) -> h5py.Group:
        """Add a die to the wafer with its properties."""
        dies_group = wafer_group['dies']
        die_group = dies_group.create_group(die_name)
        
        # Store die properties
        die_group.create_dataset('location', data=np.array(location))
        die_group.attrs['gds_file'] = np.string_(gds_file)
        die_group.attrs['die_id'] = die_id
        
        # Create junctions container group
        junctions_group = die_group.create_group('junctions')
        
        return die_group
    
    def add_junction(self, die_group: h5py.Group, junction_name: str,
                    position: Tuple[float, float], resistance_values: List[float], 
                    junction_type: str) -> h5py.Group:
        """Add a junction to a die with its measurements."""
        junctions_group = die_group['junctions']
        junction_group = junctions_group.create_group(junction_name)
        
        # Store junction properties
        junction_group.create_dataset('position', data=np.array(position))
        junction_group.create_dataset('resistance_values', data=np.array(resistance_values))
        junction_group.attrs['type'] = np.string_(junction_type)
        
        return junction_group
    
    def get_structure_info(self) -> str:
        """Print the structure of the HDF5 file."""
        def print_structure(name, obj):
            indent = "  " * name.count('/')
            if isinstance(obj, h5py.Group):
                print(f"{indent}📁 {name.split('/')[-1]}/")
                # Print attributes
                for attr_name, attr_value in obj.attrs.items():
                    print(f"{indent}  📝 {attr_name}: {attr_value}")
            else:  # Dataset
                print(f"{indent}📄 {name.split('/')[-1]} {obj.shape} {obj.dtype}")
        
        print("HDF5 File Structure:")
        self.file.visititems(print_structure)


def create_sample_wafer_file(filename: str = "wafer_measurements.h5"):
    """Create a sample HDF5 file with example data."""
    
    with WaferHDF5Manager(filename) as manager:
        # Initialize wafer
        wafer = manager.initialize_wafer("Wafer_2024_001")
        
        # Add sample dies
        sample_dies = [
            {"name": "die_001", "location": (10.5, 20.3), "gds_file": "design_A.gds", "die_id": 1},
            {"name": "die_002", "location": (30.2, 20.3), "gds_file": "design_A.gds", "die_id": 1},
            {"name": "die_003", "location": (50.1, 40.7), "gds_file": "design_B.gds", "die_id": 2},
        ]
        
        for die_info in sample_dies:
            die_group = manager.add_die(
                wafer, die_info["name"], die_info["location"],
                die_info["gds_file"], die_info["die_id"]
            )
            
            # Add sample junctions to each die
            sample_junctions = [
                {"name": "junction_001", "position": (-5.0, -3.2), 
                 "resistance": [1.23e3, 2.45e3, 1.87e3], "type": "josephson"},
                {"name": "junction_002", "position": (2.1, 4.5), 
                 "resistance": [5.67e2, 8.91e2, 6.43e2], "type": "tunnel"},
                {"name": "junction_003", "position": (0.0, 0.0), 
                 "resistance": [3.21e4, 4.56e4, 3.98e4], "type": "resistor"},
            ]
            
            for junction_info in sample_junctions:
                manager.add_junction(
                    die_group, junction_info["name"], junction_info["position"],
                    junction_info["resistance"], junction_info["type"]
                )
        
        print(f"Created sample wafer file: {filename}")
        manager.get_structure_info()


def read_wafer_data(filename: str, wafer_name: str):
    """Example function to read data from the HDF5 file."""
    
    with h5py.File(filename, 'r') as f:
        wafer_group = f[wafer_name]
        print(f"Reading data for wafer: {wafer_name}")
        print(f"Creation time: {wafer_group.attrs['creation_time']}")
        
        dies_group = wafer_group['dies']
        
        for die_name in dies_group.keys():
            die_group = dies_group[die_name]
            location = die_group['location'][()]
            gds_file = die_group.attrs['gds_file'].decode()
            die_id = die_group.attrs['die_id']
            
            print(f"\nDie: {die_name}")
            print(f"  Location: ({location[0]:.1f}, {location[1]:.1f})")
            print(f"  GDS File: {gds_file}")
            print(f"  Die ID: {die_id}")
            
            junctions_group = die_group['junctions']
            for junction_name in junctions_group.keys():
                junction_group = junctions_group[junction_name]
                position = junction_group['position'][()]
                resistance = junction_group['resistance_values'][()]
                junction_type = junction_group.attrs['type'].decode()
                
                print(f"    Junction: {junction_name}")
                print(f"      Position: ({position[0]:.1f}, {position[1]:.1f})")
                print(f"      Resistance: {resistance}")
                print(f"      Type: {junction_type}")