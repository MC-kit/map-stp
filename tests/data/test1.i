C ====================================================================== C
C Created by SuperMC/MCAM Converter, version 5.2 
C MCAM, Monte Carlo Automatic Modeling Program for Radiation Transport Codes.
C Copyright 1999-2015, FDS Team, China
C FDS Team, China.
C ACIS version:24.0.1
C ====================================================================== C
C Model Name  : /test1.i
C Start Time  : 2021/09/01 5:39:17 AM:Wednesday
C Elapsed Time: 0 seconds.
C Model Size  : 3 Cell(s), 11 Surface(s)
C
C ======================================================================
1     0   ( -5 -10 6 11 -7 8)                                       
          IMP:N=1.0  IMP:P=1.0  IMP:E=0.0 TMP=2.53005e-008   
2     0   ( -2 -3 4)                                                
          IMP:N=1.0  IMP:P=1.0  IMP:E=0.0 TMP=2.53005e-008   
3     0   ( -1 10 -9)                                               
          IMP:N=1.0  IMP:P=1.0  IMP:E=0.0 TMP=2.53005e-008   

C ===========================SURFACE Card=============================== C
1        C/Z  -0.500000000000000  0.595000000000000  0.412310562561766      
2        C/X  0.595000000000000  0.500000000000000  0.509901951359279       
3        PX   2.227000000000000                                             
4        PX   0.611000000000000                                             
5        PX   0.0                                                           
6        PX   -1.000000000000000                                            
7        PY   1.190000000000000                                             
8        PY   0.0                                                           
9        PZ   2.142000000000000                                             
10       PZ   1.000000000000000                                             
11       PZ   0.0                                                           

mode  n  
nps  10000  
phys:n  150  0  
cut:n  1.0e+99  0.0  -0.50  -0.25  0.0  
rand  gen=1  seed=19073486328125  stride=152917  hist=1  
