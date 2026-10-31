# Connecting blue-green infrastructure elements to reduce combined sewer overflows

Cavadini, Rodriguez, Cook 

EAWAG, 2024

Citation
Cavadini et al., 2024 - 10.1016/j.jenvman.2024.121465

Copyright ©, 2024, Eawag

Contact:  lauren.cook@eawag.ch, giovanbattista.cavadini@eawag.ch

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Description

This document briefly explains how to obtain the weather data from MeteoSwiss used for this study. The data cannot be openly shared by the authors, instead they need to be requested to MeteoSwiss.

1) Create an account at the MeteoSwiss website (https://www.meteoswiss.admin.ch/services-and-publications/service/weather-and-climate-products/data-portal-for-teaching-and-research.html)

2) Log in the IDAweb portal

3) Click "Station portal" 

4) Select "Kloten" as station (short name = "KLO") and continue

5) Select both "Precipitation; ten minutes total" and "Evapotranspiration; daily total" as parameters (short name for precipitation = rre150z0, short name for evapotranspiration = ets150d0) and continue

6) Select the time period. It should start before 1989 and end after 2020 (e.g. 01.01.1988-01.01.2021)

7) Proceed with the desired order. After confirming the order, you will receive an email with a link, where you can download the data

8) *Important*: save the precipitation timeseries with the name "r02.dat". The format of each line in the file should be as following: "r02 1981 1 1 0 0 0.0", which correspond to "raingauge year month day hour minute precipitation[mm]".

9) *Important*: save the evapotranspiration timeseries with the name "ET_klo.dat". The format of each line in the file should be as following: "01/01/1981	00:00	0.7", which correspond to "month/day/year hour:minute evapotranspiration[mm]".

10) Save the file in the folder "input_data_2019"
