#!/bin/bash
export NETCDF=/public/software/libs/gnu/netcdf
export PATH=$NETCDF/bin:$PATH
export LD_LIBRARY_PATH=$NETCDF/lib:$LD_LIBRARY_PATH
export CPPFLAGS='-I/usr/local/include'
export LDFLAGS='-L/usr/local/lib'

yyyymm=$1
yyyy=${1:0:4}
mm=${1:4:2}
hh=${1:8:2}

###PATH###
NOW_PATH=${yyyy}/${yyyy}${mm}/${dd}

PRODUCT_PATH=/app/data/prod

OBS_PATH=/app/data/aero_obs_month_hour/aero_obs_${yyyymm}_${hh}.NC
WORK_PATH=/app/STMAS/WORK/${mm}

# 背景场目录/产品文件名/DATA_ID
BKG_PATH=/app/data/aero_sate/aero_site_${yyyymm}.NC
file_name=aero_fuse_{yyyymm}_${hh}.NC

# 产品目录
if [ ! -d ${PRODUCT_PATH} ];
then
  mkdir -p ${PRODUCT_PATH}
fi

# 工作目录
if [ ! -d ${WORK_PATH} ];
then
  mkdir -p ${WORK_PATH}
fi

cd ${WORK_PATH}

if [ ! -f ./stmas ];
then
	ln -s /app/STMAS/stmas .
fi

# 阈值
thresh=10.0

# 编写namelist文件
cat>stmas_mg.nl<<EOF
&STMAS
numfic(1:2)=0 0
numtmf=2
lapsdt=3600
savdat=0
saveid=6
verbal=0
press_pert=1
qc_val=1
qc_std=0
maxitr=10
stmasi=1
stmasr=0.0
obsspc=1.0,1.0,3600.0
/

&VARINFO
thresh=${thresh}
needbk=1
bounds=0
radius=120
pnlt_v=0.1
lndsea=1
slevel=1
/

&FILEINFO
fbkgd='${BKG_PATH}'
fobs='${OBS_PATH}'
fout='${file_name}'
bk_varname='AERO'
obs_varname='AERO'
analysis_vanme='AERO'
FORCING_root='${PRODUCT_PATH}'
Analysis_time='${yyyymm}'
/

&Analysis_domain
lat_start = 10.0,
lon_start = 70.0,
dlat = 0.03,
dlon = 0.03,
NX_L = 2501,
NY_L = 1671,
/
EOF

./stmas

