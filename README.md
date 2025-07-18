# poverty-prober
A cheap way to convert 3D printers or manual probe machines to be fully automatic. Designed at NIST Boulder during Summer 2025 to help measure Josephson Junctions on wafer chips. I hope this code will be helpful for anyone looking for a cheap way to make an automated probe station, and please feel free to contact me with questions! I'm a highschooler, so this project is far from perfect and I'm sure there are some problems that I've yet to find. 

This prober was designed around a Prusa MK3s frame, but any printer that accepts GCODE can run the software with minor modification.

# Hardware
If you are looking to build a cheap probe station, the CAD files included can be 3D printed or machined and fitted onto a Prusa i3 MK3s. 
There are also files for parts to convert a manual prober into an automated prober.
Please refer to this Google document -> [Build Guide](https://docs.google.com/document/d/1jpKJtrroQCTVU71WwhqqQFOAk-dV8LYzDlW9VzFjXhk/edit?usp=sharing)

#Software 
This software runs on Python 3.12.2. To run it, you will most likely have to create a virtual environment. Python docs will explain it much better than I can -> [Python Docs](https://docs.python.org/3/library/venv.html)

You will need a multimeter for this project. Most lab multimeters (E.G Keithley, Agilent, Fluke) have GPIB interface built in, which this project uses for data collection. To use these, you must install National Instrument drivers -> [Download NI 488.2 Driver](https://www.ni.com/en/support/downloads/drivers/download.ni-488-2.html?srsltid=AfmBOoqDNW6VPZ1aSyrHQnoAGYbkDJ60jkX1j2CEZqXa2sz1cAuOPGQv#559044)

To run the GDSpy library used for reading GDS files, you will also need to install Visual Studio C++ Build Tools -> [Install here](https://visualstudio.microsoft.com/downloads/?q=build+tools)

# Using the automated prober
I've tried to make operation as not confusing as possible, but I am not very good at that. Please refer to this Google Document with detailed picture instructions for how to operate your probe machine, as well as how to use the software and read measurements -> (Instructions)[https://docs.google.com/document/d/1vez7zo_DF2WveKpVUwSjUk-TLnuJKJ8-mlyRiejgi00/edit?usp=sharing]

# Conclusion
Please feel free to reach out to me through my email awsome.arthur01@gmail.com for any inquiries or problems with this project. In the off chance that anyone ever even sees this project and chooses to build one, I am more than willing to help out with any problems. Hope you enjoy!
