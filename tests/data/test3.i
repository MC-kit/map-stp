C ====================================================================== C
C Created by SuperMC/MCAM Converter, version 5.2
C MCAM, Monte Carlo Automatic Modeling Program for Radiation Transport Codes.
C Copyright 1999-2015, FDS Team, China
C FDS Team, China.
C ACIS version:24.0.1
C ====================================================================== C
C Model Name  : /test2-with-void.i
C Start Time  : 2021/09/01 5:43:24 AM:Wednesday
C All Elapsed Time: 0 seconds.
C Solids Analysis Time��0 seconds.
C Model Size  : 3 Cell(s), 17 Surface(s)
C
C ======================================================================
1     0   ( -6 -15 7 16 -10 11)
          IMP:N=1.0  IMP:P=1.0  IMP:E=0.0 TMP=2.53005e-008
2     0   ( -2 -4 5)
          IMP:N=1.0  IMP:P=1.0  IMP:E=0.0 TMP=2.53005e-008
3     0   ( -1 15 -14)
          IMP:N=1.0  IMP:P=1.0  IMP:E=0.0 TMP=2.53005e-008
4     0   ( -3 8 -9 12 -13 17 )((6:15:-7:-16:10:-11))((2:4:-5))((1
          :-15:14))
          IMP:N=1.0  IMP:P=1.0  IMP:E=0.0            $void reach face limit
5     0   (13:-17:-12:-8:9:3)
          IMP:N=0  IMP:P=0  IMP:E=0
          $The outer cell

C ===========================SURFACE Card=============================== C
1        C/Z  -0.500000000000000  0.595000000000000  0.412310562561766
2        C/X  0.595000000000000  0.500000000000000  0.509901951359279
3        PX   103.000000000000000
4        PX   2.227000000000000
5        PX   0.611000000000000
6        PX   0.0
7        PX   -1.000000000000000
8        PX   -101.000000000000000
9        PY   102.000000000000000
10       PY   1.190000000000000
11       PY   0.0
12       PY   -100.000000000000000
13       PZ   103.000000000000000
14       PZ   2.142000000000000
15       PZ   1.000000000000000
16       PZ   0.0
17       PZ   -101.000000000000000

mode  n
nps  10000
phys:n  150  0
cut:n  1.0e+99  0.0  -0.50  -0.25  0.0
rand  gen=1  seed=19073486328125  stride=152917  hist=1
