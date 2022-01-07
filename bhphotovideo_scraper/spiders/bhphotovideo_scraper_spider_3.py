import scrapy, json
import unicodedata, json
from collections import OrderedDict
from scrapy import Request

class bhphotovideo_scraper(scrapy.Spider):

	name = "bhphotovideo_scraper_3"

	# start_urls = ('https://www.bhphotovideo.com/c/browse/Video/ci/2873/N/4294246899','https://www.bhphotovideo.com/c/browse/used-mobile-devices/ci/27595/N/3801316913',
	# 			  'https://www.bhphotovideo.com/c/browse/Computers-Accessories/ci/15241/N/4294210528', 'https://www.bhphotovideo.com/c/browse/Pro-Audio/ci/2875/N/4294246787',
	# 			  'https://www.bhphotovideo.com/c/browse/A-V-Presentation/ci/2874/N/4294246800', 'https://www.bhphotovideo.com/c/browse/Home-Portable-Entertainment/ci/15240/N/4294210561')

	### test ###
	# start_urls = ['https://www.bhphotovideo.com/c/browse/Computers-Accessories/ci/15241/N/4294210528']
	start_urls = [
		# 'https://www.bhphotovideo.com/c/browse/Computers-Accessories/ci/15241/N/4294210528',
					# 'https://www.bhphotovideo.com/c/browse/Home-Portable-Entertainment/ci/15240/N/4294210561',
					'https://www.bhphotovideo.com/c/buy/Projectors/ci/3010/N/4040858883',
					# 'https://www.bhphotovideo.com/c/browse/specials/ci/36896/N/3503162427'
				  ]

	################

	use_selenium = True
	total_count = 0
	bhnum_list = []

	def start_requests(self):
		for url in self.start_urls:
			yield Request(url, callback=self.parseSubCat)
			# break

	# def parseCat1(self, response):
	# 	categories = response.xpath('//ul[@class="nav-E capital"]/li/a/@href').extract()
	# 	for cat_url in categories:
	# 		yield Request(cat_url, callback=self.parseCat, meta={"CatURL": cat_url, 'page_num':1})

	# def parseCat(self, response):
	# 	categories = response.xpath('//li[@class="clp-category"]/a/@href').extract()
	# 	links = []
	# 	# print len(categories)
	#
	# 	if not categories:
	# 		yield Request(response.url, callback=self.parseSubCat, meta={"CatURL": response.url, 'page_num':1}, dont_filter=True)
	# 	else:
	# 		for cat_url in categories:
	# 			if 'http' not in cat_url:
	# 				continue
	# 			# if '3756184938' not in cat_url:
	# 			# 	continue
	# 			yield Request(cat_url, callback=self.parseSubCat, meta={"CatURL": cat_url, 'page_num':1})

			# break

		########### test ############
		# cat_url = 'https://www.bhphotovideo.com/c/buy/Projectors/ci/3010/N/4040858883'
		# yield Request(cat_url, callback=self.parseSubCat, meta={"CatURL": cat_url, 'page_num':1})
		################################

	def parseSubCat(self, response):
		sub_categories = response.xpath('//a[@data-selenium="categoryGroupLink"]/@href').extract()
		# print len(sub_categories)

		if sub_categories:
			for sub_cat_url in sub_categories:
				# if 'http' not in sub_cat_url:
				# 	continue
				yield Request(response.urljoin(sub_cat_url), callback=self.parseSubCat, meta={"CatURL": sub_cat_url, 'page_num':1})

				# break
		else:
			products = response.xpath('//div[@data-selenium="miniProductPageProduct"]')
			print(str(len(products)))
			item_cat = response.xpath('//a[@data-selenium="linkCrumb"]/text()').extract()[-1]

			for product in products:
				itemdata = product.xpath('./@data-itemdata').extract_first()
				itemdata_json = {}
				if product.xpath('.//span[@data-selenium="uppedDecimalPriceFirst"]/text()').re(r'[\d.,]+'):
					uppedDecimalPriceFirst = \
						product.xpath('.//span[@data-selenium="uppedDecimalPriceFirst"]/text()').re(r'[\d.,]+')[0]
					uppedDecimalPriceSecond = \
						product.xpath('.//sup[@data-selenium="uppedDecimalPriceSecond"]/text()').re(r'[\d.,]+')[0]
					itemdata_json['price'] = uppedDecimalPriceFirst + '.' + uppedDecimalPriceSecond

				product_url = product.xpath('.//a[@data-selenium="miniProductPageProductNameLink"]/@href').extract_first()
				item_cond = product.xpath('.//button[@data-selenium="miniProductPageUsedItemConditionBtn"]/text()').extract_first()

				if item_cond:
					item_cond = item_cond.strip()

				yield Request(response.urljoin(product_url), callback=self.parseProduct, meta={"itemdata": itemdata_json, 'item_cat': item_cat, 'item_cond': item_cond, 'page_num':1}, dont_filter=True)
				# break

			next_page = response.xpath('//a[@data-selenium="listingPagingPageNext"]/@href').extract_first()
			if next_page:
				yield Request(response.urljoin(next_page), callback=self.parseSubCat, meta={"CatURL": next_page, 'page_num':1})

	def parseProduct(self, response):
		if response.url =='https://www.bhphotovideo.com/c/product/801817515-USE/panasonic_pt_rz370u_solid_shine_dlp.html':
			pass

		data = response.text.split('window.__PRELOADED_DATA = ')[-1].split(';window.__SERVER_RENDER_TIME = ')[0]
		data = data.replace('false', '0').replace('null', '0').replace('true', '1')
		json_data = json.loads(response.xpath(
			'//section[@class="app-layout"]/div/script[@type="application/ld+json" and contains(text(),"Product")]/text()').extract_first())
		itemdata = response.meta["itemdata"]

		item = OrderedDict()

		part_num = json_data.get('mpn')

		if not part_num:
			print('No partNumber 1: ' + response.url)
			return

		item['partNumber'] = part_num
		item['URL'] = response.url

		item['Title'] = json_data['name']

		item['Manufacturer'] = json_data['brand']['name']
		item['BH Num'] = json_data['sku']
		item['Condition'] = response.meta["item_cond"]
		item['Description'] = json_data.get('description')

		list_price = response.xpath('//div[@data-selenium="pricingPrice"]/text()').re(r'[\d.,]+')
		if list_price:
			list_price = list_price[0]
		else:
			list_price = ''
		item['List Price'] = list_price

		if 'price' in itemdata.keys():
			item['Sale Price'] = itemdata['price']
		else:
			item['Sale Price'] = ''

		bhSku = json_data['sku']

		if bhSku not in self.bhnum_list:

			image_url = json_data['image']
			item['ImageURL'] = image_url

			if image_url:
				image_file_name = image_url.split('/')[-1]
				item['FileName'] = image_file_name
			else:
				item['FileName'] = ''

			item['Quantity'] = response.xpath('//button[@data-selenium="quantityInfoButton"]/text()').extract_first()
			item['Category'] = response.meta["item_cat"]

			overviews = response.xpath('//div[@data-selenium="overviewLongDescription"]/div/p//text()').extract()
			item['OverView'] = ''.join(overviews)
			ov_str = ''
			# try:
			# 	ov_descs = all_json['ProductStore']['productContextData']['REGULAR']['overview']['data']['items'][0]['features']['featureGroups'][0]['features']
			# 	if ov_descs:
			# 		a = []
			# 		for ov in ov_descs:
			# 			a.append(ov['title'])
			# 			a.append(ov['description'])
			# 		item['OverView'] = '\n'.join(a)
			# except:
			# 	pass

			weight = ''
			dimensions = ''
			spec_result = ''

			spec_tags = response.xpath('//tr[@data-selenium="specsItemGroupTableRow"]')
			for spec_tag in spec_tags:
				spec_name = spec_tag.xpath(
					'./td[@data-selenium="specsItemGroupTableColumnLabel"]/text()').extract_first()
				spec_val = spec_tag.xpath(
					'./td[@data-selenium="specsItemGroupTableColumnValue"]/span/text()').extract_first()

				if spec_name == 'Dimensions':
					dimensions = spec_val
				elif spec_name == 'Weight':
					weight = spec_val

				if (not spec_name) or (not spec_val):
					continue
				spec_result += spec_name + ': ' + spec_val + '.'

			# try:
			# 	specBody = all_json['ProductStore']['productContextData']['REGULAR']['specifications']['data']['items'][0]['groups'][0]['specs']
			#
			# 	for specs in specBody:
			# 		spec_name = specs['name']
			# 		spec_val = specs['value']
			#
			# 		spec_result += spec_name + ': ' + spec_val + '.'
			#
			# 		if spec_name == 'Dimensions':
			# 			dimensions = spec_val
			# 		elif spec_name == 'Weight':
			# 			weight = spec_val
			# except:
			# 	pass

			item['Specs'] = spec_result
			item['Width*Height*Depth'] = dimensions


			if weight:
				weight = weight.strip()
				if 'oz' in weight:
					weight = 1
				else:
					weight = unicodedata.normalize('NFKD', weight).encode('ascii', 'ignore').decode("utf-8").split(' ')[
						0]
					try:
						test = float(weight)
					except:
						weight = ''

			item['Weight'] = weight

			item['Additional Comments'] = response.xpath(
				'//div[@data-selenium="usedItemConditionFullDescription"]/text()').extract_first()

			self.total_count += 1
			print('\n##################################\ntotal count: ' + str(
				self.total_count) + '\n##################################\n')
			yield item
		else:
			i = 1
			print('same bhnum: ' + bhSku)
		# try:
		# 	all_json = json.loads(data)
		#
		#
		# 	else:
		# 		i = 1
		# 		print('same bhnum: ' + bhSku)
		# except:
		# 	itemdata = response.meta["itemdata"]
		#
		# 	item = OrderedDict()
		#
		# 	part_num = response.xpath('//span[@data-selenium="sku"]/text()').extract_first()
		#
		# 	if not part_num:
		# 		print('No partNumber 2: ' + response.url)
		# 		return
		#
		# 	item['partNumber'] = part_num
		# 	item['URL'] = response.url
		#
		# 	item['Title'] = ''
		# 	brand = response.xpath('//span[@itemprop="name"]/text()').extract_first()
		# 	if brand:
		# 		item['Title'] = brand.strip()
		#
		# 	item['Manufacturer'] = ''
		# 	brand = response.xpath('//span[@itemprop="brand"]/text()').extract_first()
		# 	if brand:
		# 		item['Manufacturer'] = brand
		#
		# 	bhSku = response.xpath('//span[@data-selenium="itemcodebh"]/text()').extract_first()
		# 	# if bhSku:
		# 	# 	bhSku = unicodedata.normalize('NFKD', bhSku).encode('ascii','ignore').decode("utf-8").strip().split(' ')[-1]
		# 	# else:
		# 	# 	bhSku = ''
		#
		# 	if bhSku not in self.bhnum_list:
		# 		item['BH Num'] = bhSku
		#
		# 		item['Condition'] = response.meta["item_cond"]
		#
		# 		descs = response.xpath('//ul[@data-selenium="highlightList"]/li/text()').extract()
		# 		desc = ""
		# 		if descs:
		# 			desc = '. '.join(descs) + '.'
		# 		item['Description'] = desc
		#
		# 		list_price = response.xpath('//a[@data-selenium="buyUsedLink"]/span/text()').re(r'[\d.,]+')
		# 		if list_price:
		# 			list_price = list_price[0]
		# 		else:
		# 			list_price = ''
		# 		item['List Price'] = list_price
		#
		# 		if 'price' in itemdata.keys():
		# 			item['Sale Price'] = itemdata['price']
		# 		else:
		# 			item['Sale Price'] = ''
		#
		# 		image_url = response.xpath('//img[@data-selenium="imgLoad"]/@src').extract_first()
		# 		item['ImageURL'] = image_url
		#
		# 		if image_url:
		# 			image_file_name = image_url.split('/')[-1]
		# 			item['FileName'] = image_file_name
		# 		else:
		# 			item['FileName'] = ''
		#
		# 		item['Quantity'] = response.xpath('//input[@data-selenium="qty-box"]/@value').extract_first()
		# 		item['Category'] = response.meta["item_cat"]
		#
		# 		ov_descs = response.xpath('//p[@class="ov-desc-paragraph"]//text()').extract()
		# 		item['OverView'] = ''
		# 		ov_str = ''
		# 		if ov_descs:
		# 			for ov in ov_descs:
		# 				ov_str += ov.strip().replace('\n', ' ').replace('\r', ' ') + ' '
		# 			item['OverView'] = ov_str
		#
		#
		# 		specBody = response.xpath('//tbody[@data-selenium="specBody"]/tr')
		#
		# 		weight = ''
		# 		dimensions = ''
		#
		#
		# 		spec_result = ''
		#
		# 		for specs in specBody:
		# 			if not specs.xpath('./td[@data-selenium="specTopic"]/text()').extract_first():
		# 				continue
		# 			spec_name = specs.xpath('./td[@data-selenium="specTopic"]/text()').extract_first().strip()
		#
		# 			specDetails = specs.xpath('./td[@data-selenium="specDetail"]//text()').extract()
		# 			spec_list = []
		# 			for s in specDetails:
		# 				spec_list.append(s.strip())
		#
		# 			spec_result += spec_name + ': ' + ' '.join(spec_list) + '.'
		#
		# 			if spec_name == 'Dimensions':
		# 				dimensions = ' '.join(spec_list)
		# 			elif spec_name == 'Weight':
		# 				weight = ' '.join(spec_list)
		#
		# 		item['Specs'] = spec_result
		# 		item['Width*Height*Depth'] = dimensions
		#
		# 		weight = weight.strip()
		# 		if weight:
		# 			if 'oz' in weight:
		# 				weight = 1
		# 			else:
		# 				weight = unicodedata.normalize('NFKD', weight).encode('ascii','ignore').decode("utf-8").split(' ')[0]
		# 				try:
		# 					test = float(weight)
		# 				except:
		# 					weight = ''
		#
		#
		# 		item['Weight'] = weight
		#
		#
		# 		item['Additional Comments'] = response.xpath('//span[@class="additionComments"]/text()').extract_first()
		#
		# 		self.total_count += 1
		# 		print('\n##################################\ntotal count: ' + str(self.total_count) + '\n##################################\n')
		# 		yield item
		# 	else:
		# 		i = 1
		# 		print('same bhnum: ' + bhSku)















