import netCDF4 as nc
import xarray as xr
import numpy as np
from settings import LAT, LON, RANGE_QINGHAI, colors, clevs
from plot import plot_contourf_grid_colors
import pygrib

from scipy.interpolate import griddata

from date_util import add_one_day_to_string
import os

def createpath(path):
    if not path.endswith("/"):
        path = os.path.dirname(path)
        if not os.path.exists(path):
            os.makedirs(path)
    else:
        if not os.path.exists(path):
            os.makedirs(path)

class Inpter():

	def __init__(self, lat, lon, lat2, lon2):
		self.olons, self.olats = np.meshgrid(lon2, lat2)
		lons, lats = np.meshgrid(lon, lat)
		lons, lats = lons.flatten()[:, None], lats.flatten()[:, None]
		self.point = np.hstack((lons, lats))

	def linear(self, value):
		results = griddata(self.point, values=value.flatten(), xi=(self.olons, self.olats), method='linear')
		return results.flatten()


def writeNC(datas, LON, LAT, outfile):
	createpath(outfile)
	da = nc.Dataset(outfile, 'w', format='NETCDF3_CLASSIC')
	try:
		dlat = da.createDimension('LAT', len(LAT))
		dlon = da.createDimension('LON', len(LON))
		lon = da.createVariable('LON', 'f4', ('LON'))
		lat = da.createVariable('LAT', 'f4', ('LAT'))
		da.variables['LAT'][:] = LAT
		da.variables['LON'][:] = LON
		lon.units = 'degrees east'
		lat.units = 'degrees north'
		dataV = da.createVariable('AERO', 'f4', ('LAT', 'LON'), zlib=True, complevel=3)
		dataV.fillvalue = '-999.0'
		dataV[:, :] = datas[:, :]
		print('save the file:', outfile)
	except Exception as e:
		raise e
	finally:
		da.close()


def write(datas, data_lon, data_lat, outfile):
	createpath(outfile)
	da = nc.Dataset(outfile, 'w', format='NETCDF3_CLASSIC')
	try:
		dlat = da.createDimension('latitude', len(data_lat))
		dlon = da.createDimension('longitude', len(data_lon))
		lat = da.createVariable('latitude', 'f4', ('latitude'))
		lon = da.createVariable('longitude', 'f4', ('longitude'))
		da.variables['latitude'][:] = data_lat
		da.variables['longitude'][:] = data_lon
		lon.units = 'degrees east'
		lat.units = 'degrees north'
		dataV = da.createVariable('PRE', 'f4', ('latitude', 'longitude'), zlib=True, complevel=3)
		dataV.fillvalue = '-999.0'
		dataV[:, :] = datas[:, :]
		print('save the file:', outfile)
	except Exception as e:
		print(e)
		raise e

	finally:
		da.close()


LONS, LATS = np.meshgrid(LON, LAT)


def read_grid(fi, ):
	try:
		# 打开 GRIB 文件
		grbs = pygrib.open(fi)
		# 选择第一条消息（变量）
		# grb = grbs[85]
		grb = grbs.select(shortName='blh')[0]
		# # 提取变量数据
		variable_data = grb.values  # 变量值（二维数组）
		date = grb.validDate
		lats = grb.latlons()[0].T[0]  # 经纬度数据（二维数组）
		lons = grb.latlons()[1][0]
		# print("Latitudes:\n", lats)
		# print("Longitudes:\n", lons)

		index_lon = np.where((lons >= RANGE_QINGHAI[0] - 0.5) & (lons <= RANGE_QINGHAI[1] + 0.5))
		index_lat = np.where((lats >= RANGE_QINGHAI[2] - 0.5) & (lats <= RANGE_QINGHAI[3] + 0.5))
		lats = lats[index_lat]
		lons = lons[index_lon]

		blh_data = variable_data[index_lat[0], index_lon[0][0]:index_lon[0][-1] + 1]
		# 关闭文件
		grbs.close()
		return blh_data, lons, lats, date
	except Exception as e:
		print(e)
		return None, None, None, None


if __name__ == '__main__':
	# ec_path = 'F:\\mounth_data\\blk_2023-10.nc'
	# aero_path = 'E:\\data\\aero\\sate\\MERRA2_400.tavgM_2d_aer_Nx.202310.nc4.nc4'
	# # ec_path = '/app/data/blk_2024-12.nc'
	# out_path = 'E:\\data\\aero\\aero_site_2023-10.NC'
	# out_path = '/app/data/aero_site.NC'

	sate_dir = "F:/sate/L3_2023/"
	ec_dir = "F:/link_dir/"
	out_dir = "F:/sate_aero_obs/"

	out_png_dir = "F:/sate_aero_obs_png/"

	for root, subdirs, files in os.walk(sate_dir):
		for file in files:
			sate_path = os.path.join(root, file)
			date_ymd = file.split('.')[0].split('_')[1]
			date_hm = file.split('.')[0].split('_')[2]
			date_h_int = int(date_hm)
			sate_date_str = date_ymd + date_hm
			era_ymd = date_ymd
			if date_h_int >= 0 and date_h_int <= 3:
				era_h = '00'
			elif date_h_int >= 4 and date_h_int <= 9:
				era_h = '06'
			elif date_h_int >= 10 and date_h_int <= 15:
				era_h = '12'
			elif date_h_int >= 16 and date_h_int <= 21:
				era_h = '18'
			elif date_h_int >= 22 and date_h_int <= 23:
				era_h = '00'
				era_ymd = add_one_day_to_string(date_ymd, '%Y%m%d')
			# ERA5-surface-2021010612.grib
			ec_path = os.path.join(ec_dir, 'ERA5-surface-' + era_ymd + era_h + '.grib')

			if os.path.exists(ec_path) == False:
				continue
			try:
				blh_data, lons_blk,lats_blk, date = read_grid(ec_path)
				#转换成km
				blh_data = blh_data/1000.0
				# 方法1：直接通过变量名访问（需确保变量名正确）
				print('blh_data----', blh_data.shape)
				date_str = era_ymd + era_h
				blk_png_path = os.path.join(out_png_dir + '/' + date_ymd + '/', 'blk_' + date_str + '.png')
				blk_cz_png_path = os.path.join(out_png_dir + '/' + date_ymd + '/' , 'blk_' + date_str + '_插值后的.png')
				createpath(blk_png_path)
				# 初始化插值
				Ip = Inpter(lats_blk, lons_blk, LAT, LON)
				blh_data_inpter = Ip.linear(blh_data)
				blh_data_inpter = blh_data_inpter.reshape((len(LAT), len(LON)))

				lons_blk, lats_blk = np.meshgrid(lons_blk, lats_blk)
				plot_contourf_grid_colors(lons_blk, lats_blk, blh_data, blk_png_path, RANGE_QINGHAI, colors, clevs, 0, '边界层高度（单位km）', 5,
				                   0, 0,
				                   is_draw_grid=True)

				# 插值后出图
				plot_contourf_grid_colors(LONS, LATS, blh_data_inpter, blk_cz_png_path, RANGE_QINGHAI, colors, clevs, 0,
				                   '边界层高度（单位km）', 5, 0, 0,
				                   is_draw_grid=True)

				# aero_path = '/app/data/MERRA2_400.tavgM_2d_aer_Nx.202412.nc4.nc4'
				aero_data = xr.open_dataset(sate_path)
				lats_tot = aero_data['latitude'].values.squeeze()
				lons_tot = aero_data['longitude'].values.squeeze()
				TOTEXTTAU = aero_data['AOT_Pure'].values.squeeze()

				index_lon = np.where((lons_tot >= RANGE_QINGHAI[0] - 1) & (lons_tot <= RANGE_QINGHAI[1] + 1))
				index_lat = np.where((lats_tot >= RANGE_QINGHAI[2] - 1) & (lats_tot <= RANGE_QINGHAI[3] + 1))
				lats_tot = lats_tot[index_lat]
				lons_tot = lons_tot[index_lon]

				TOTEXTTAU = TOTEXTTAU[index_lat[0], index_lon[0][0]:index_lon[0][-1] + 1]
				# TOTSCATAU = TOTSCATAU[index_lat[0], index_lon[0][0]:index_lon[0][-1] + 1]

				# print(lons)
				# print(lats)
				print(TOTEXTTAU)
				# print(TOTSCATAU)

				# 初始化插值
				Ip = Inpter(lats_tot, lons_tot, LAT, LON)
				TOTEXTTAU_Inpter = Ip.linear(TOTEXTTAU)
				TOTEXTTAU_Inpter = TOTEXTTAU_Inpter.reshape((len(LAT), len(LON)))
				# TOTSCATAU = Ip.linear(TOTSCATAU)
				# print(TOTEXTTAU)
				# print(len(TOTEXTTAU))
				# print(TOTSCATAU)
				# print(len(TOTSCATAU))
				# 数据纬度方向是从小到大的
				# 数据分辨率，纬度方向是0.5度，经度方向是0.625度
				lonsin, latsin = np.meshgrid(lons_tot, lats_tot)


				sate_png_path = os.path.join(out_png_dir+ '/' + date_ymd + '/' , 'sate_AOT_' + sate_date_str + '.png')
				plot_contourf_grid_colors(lonsin, latsin, TOTEXTTAU, sate_png_path, RANGE_QINGHAI,  colors, clevs, 0, 'AOT',
				                   5, 0, 0,
				                   is_draw_grid=True)

				sate_cz_png_path = os.path.join(out_png_dir + '/' + date_ymd + '/' , 'sate_AOT_' + sate_date_str + '_插值后的.png')
				plot_contourf_grid_colors(LONS, LATS, TOTEXTTAU_Inpter, sate_cz_png_path, RANGE_QINGHAI, colors, clevs,0,
				                   'AOT',
				                   5, 0, 0,
				                   is_draw_grid=True)

				# 需要反转下数据
				# blh_data = blh_data[::-1, :]
				data_sate = (TOTEXTTAU_Inpter / blh_data_inpter)
				data_sate = data_sate.astype(np.float64)
				# 纬度方向反转
				# data_sate = data_sate[::-1, :]
				out_path = os.path.join(out_dir + '/' + date_ymd + '/' , 'aero_site_' + sate_date_str + '.NC')
				writeNC(data_sate, LON, LAT, out_path)
				# writeNC(data_sate, LON, LAT, out_path)

				aero_sate_png_path = os.path.join(out_png_dir + '/' + date_ymd + '/' , 'sate_' + sate_date_str + '.png')
				plot_contourf_grid_colors(LONS, LATS, data_sate, aero_sate_png_path, RANGE_QINGHAI, colors, clevs, 0,
				                          '卫星-气溶胶消光系数', 5,
				                          0, 0, is_draw_grid=True)
			except Exception as e:
				print(e)
				continue
