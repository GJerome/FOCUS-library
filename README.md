# FOCUS

## The project
The goal of this project is to combine materials science and nanophotonics to overcome the low energy density of sunlight for solar cell applications. To mitigate this issue, various solutions have been proposed, such as increasing the efficiency of solar cells or using solar concentrators.

Our approach starts with halide perovskites, a class of versatile semiconductor in which we can tune the bandgap and locally change their composition under illumination. The study and characterization of the entangled process regulating this behavior spans in timescales ranging from femtosecond to minutes and requires a suit of homebuilt tools and great expertise in material science. The halide perovskites are then integrated into our nanophotonic design to collect diffuse light, concentrate it in our material and collimate the quasi-monochromatic emission. At its core, we are creating an integrated device with an extreme asymmetry between the absorption cross section and the emission. To this end we developed an ultrafast optical toolbox able to measure TRPL, automated mapping PLQY over mm scale with nm precision, TA (in progress), Ramman (in progress), microscopy in real and Fourier space with temperature control and under an inert atmosphere.  

## The repository
This repository contains all the library and python wrappers allowing us to control the Syracuse optical setup at the Nanoscale Solar Cells laboratory at Amolf. It is currently a work in progress, as many instruments are still being integrated into different experiment. The main goal of this repository is remote collaboration and project tracking.

The following instruments are incorporated into our workflow:
HDPTA (via RemoteEx) and subsequent n-exponential fitting
- Lock-in amplifier (UHFLI 600 MHz)
- Lightfield integration
- Kymera 193i spectrometer 
- SR542 precision optical chopper
- DL225 Newport delay line
- Coherent laser and associated pulse picker 
- Various thorlabs shutters, flip mount, and filter wheel
- Rough and precise automated stage
