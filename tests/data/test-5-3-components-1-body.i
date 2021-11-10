C ====================================================================== C
C Created by SuperMC/MCAM Converter, version 5.2
C MCAM, Monte Carlo Automatic Modeling Program for Radiation Transport Codes.
C Copyright 1999-2015, FDS Team, China
C FDS Team, China.
C ACIS version:24.0.1
C ====================================================================== C
C Model Name  : /test-5-3-components-1-body.i
C Start Time  : 2021/11/07 11:46:33 PM:Sunday
C All Elapsed Time: 0 seconds.
C Solids Analysis Time��0 seconds.
C Model Size  : 3 Cell(s), 16 Surface(s)
C
C ======================================================================
2000   0   ( 2010 2006 -2009 -2005 -2001 2002)
          IMP:N=1.0  IMP:P=1.0  IMP:E=0.0 TMP=2.53005e-008
2001   0   ( 2012 2006 -2011 -2005 -2001 2002)
          IMP:N=1.0  IMP:P=1.0  IMP:E=0.0 TMP=2.53005e-008
2002   0   ( 2014 2006 -2013 -2005 -2001 2002)
          IMP:N=1.0  IMP:P=1.0  IMP:E=0.0 TMP=2.53005e-008
2003   0   ( -2000 2003 -2004 2007 -2008 2015 )((-2010:-2006:2009
          :2005:2001:-2002))((-2012:-2006:2011:2005:2001:-2002))((-2014
          :-2006:2013:2005:2001:-2002))
          IMP:N=1.0  IMP:P=1.0  IMP:E=0.0            $void reach face limit
2004   0   (2008:-2015:-2007:-2003:2004:2000)
          IMP:N=0  IMP:P=0  IMP:E=0
          $The outer cell

C ===========================SURFACE Card=============================== C
2000     PX   100.000000000000000
2001     PX   -0.153000000000000
2002     PX   -2.400000000000000
2003     PX   -103.000000000000000
2004     PY   102.000000000000000
2005     PY   1.710000000000000
2006     PY   0.0
2007     PY   -100.000000000000000
2008     PZ   100.000000000000000
2009     PZ   -0.100000000000000
2010     PZ   -2.000000000000000
2011     PZ   -3.100000000000000
2012     PZ   -5.000000000000000
2013     PZ   -6.100000000000000
2014     PZ   -8.000000000000000
2015     PZ   -108.000000000000000

mode  n
nps  10000
phys:n  150  0
cut:n  1.0e+99  0.0  -0.50  -0.25  0.0
rand  gen=1  seed=19073486328125  stride=152917  hist=1
