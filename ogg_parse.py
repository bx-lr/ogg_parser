import os, sys
import struct
import binascii
import re

#Oggs
OGGMAGIC = 0x4f676753	

#32bit size 
DEFAULTSIZE = 0x04

#multiple a/v encoding methods are supported in a single ogg
ENCODER = ""

#vorbis identification header
TYPE1 = 1
#vorbis comment header
TYPE3 = 3
#vorbis setup header
TYPE5 = 5

MASK = [0x00000000,0x00000001,0x00000003,0x00000007,0x0000000f,\
 0x0000001f,0x0000003f,0x0000007f,0x000000ff,0x000001ff,\
 0x000003ff,0x000007ff,0x00000fff,0x00001fff,0x00003fff,\
 0x00007fff,0x0000ffff,0x0001ffff,0x0003ffff,0x0007ffff,\
 0x000fffff,0x001fffff,0x003fffff,0x007fffff,0x00ffffff,\
 0x01ffffff,0x03ffffff,0x07ffffff,0x0fffffff,0x1fffffff,\
 0x3fffffff,0x7fffffff,0xffffffff]


class OggBuffer:
	def __init__(self, data):
		self.data = data
		self.size = len(data)
		self.refcount = 1
		self.owner = 0
		self.next = 0

	def pprint(self):
		print "OggBuffer data =", self.data[0:12]
		print "OggBuffer size = ", self.size
		print "OggBuffer refcount = ", self.refcount
		print "OggBuffer owner = ", self.owner
		print "OggBuffer next = ", self.next

class OggReference:
	def __init__(self, data):
		self.buffer = OggBuffer(data)
		self.begin = 0
		self.length = self.buffer.size
		self.next = 0

	def pprint(self):
		print "OggReference buffer =", self.buffer
		print "OggReference begin = ", self.begin
		print "OggReference length = ", self.length
		self.buffer.pprint()


class OggpackBuffer:
	def __init__(self):
		self.headbit = 0
		self.headptr = 0
		self.headend = 0
		self.count = 0
		self.head = 0
		self.tail = 0 

	def pprint(self):
		print "OggpackBuffer headbit =", self.headbit
		print "OggpackBuffer headptr = ", self.headptr[0:12]
		print "OggpackBuffer headend = ", self.headend
		print "OggpackBuffer count = ", self.count
		print "OggpackBuffer head = ", self.head
		print "OggpackBuffer tail = ", self.tail

class Codebook:
	def __init__(self):
		self.dec_maxlength = 0
		self.dec_table = 0
		self.dec_method = 0
		self.dec_type = 0 
			# 0 = entry number
			# 1 = packed vector of values
			# 2 = packed vector of column offsets, maptype 1
			# 3 = scalar offset into value array,  maptype 2 
		self.q_bits = 0
		self.dim = 0 	# codebook dimensions (elements per vector) 
		self.q_delp = 0
		self.q_minp = 0
		self.q_del = 0
		self.q_min = 0
		self.q_seq = 0
		self.q_pack = 0
		self.q_val = 0
		self.used_entries = 0 # populated codebook entries 
		self.dec_buf = 0

		#  C only 
		self.dec_nodeb = 0
		self.dec_leafw = 0

		self.entries = 0  #  codebook entries 

	def pprint(self):
		print "Codebook dec_maxlength = ", self.dec_maxlength
		print "Codebook dec_table = ", self.dec_table
		print "Codebook dec_method = ",  self.dec_method
		print "Codebook dec_type =  ", self.dec_type
		print "Codebook q_bits = ", self.q_bits
		print "Codebook dim = ", self.dim
		print "Codebook q_delp = ", self.q_delp
		print "Codebook q_minp = ", self.q_minp
		print "Codebook q_del = ", self.q_del
		print "Codebook q_min = ", self.q_min
		print "Codebook q_seq = ", self.q_seq
		print "Codebook q_pack = ", self.q_pack
		print "Codebook q_val = ", self.q_val
		print "Codebook used_entries = ", self.used_entries
		print "Codebook dec_buf = ", self.dec_buf
		print "Codebook dec_nodeb = ",  self.dec_nodeb
		print "Codebook dec_leafw = ", self.dec_leafw
		print "Codebook entries = ", self.entries

class Vorbis:
	def __init__(self):
		self.type1 = ""
		self.type3 = ""
		self.type5 = []

	def pprint(self):
		print "self.type1", binascii.hexlify(self.type1)
		print "self.type3", binascii.hexlify(self.type3)
		print "len self.type5", len(self.type5)
		print "self.type5[0]", binascii.hexlify(self.type5[0])
		print "self.type5[1]", binascii.hexlify(self.type5[1])

class VorbisType1:
	def __init__(self, data):
		self.offset = 0
		self.data = data
		self.type = struct.unpack("B", data[self.offset])[0]
		self.offset += DEFAULTSIZE / 4

		self.codec = struct.unpack("6s", data[self.offset:self.offset + (DEFAULTSIZE / 4) * 6])
		self.offset += (DEFAULTSIZE / 4) * 6

		self.vorbis_version = struct.unpack("<I", data[self.offset:self.offset + DEFAULTSIZE])[0]
		self.offset += DEFAULTSIZE

		self.audio_channels = struct.unpack("B", data[self.offset:self.offset + DEFAULTSIZE / 4])[0]
		self.offset += DEFAULTSIZE / 4

		self.audio_sample_rate = struct.unpack("<I", data[self.offset:self.offset + DEFAULTSIZE])[0]
		self.offset += DEFAULTSIZE

		self.bitrate_max = struct.unpack("<I", data[self.offset:self.offset + DEFAULTSIZE])[0]
		self.offset += DEFAULTSIZE

		self.bitrate_nom = struct.unpack("<I", data[self.offset:self.offset + DEFAULTSIZE])[0]
		self.offset += DEFAULTSIZE

		self.bitrate_min = struct.unpack("<I", data[self.offset:self.offset + DEFAULTSIZE])[0]
		self.offset += DEFAULTSIZE

		bits = split_byte(struct.unpack("B", data[self.offset:self.offset + DEFAULTSIZE/4])[0])
		self.blocksize_0 = bits[1]
		self.blocksize_1 = bits[0]
		self.offset += DEFAULTSIZE / 4

		self.framing_flag = struct.unpack("B", data[self.offset:self.offset + DEFAULTSIZE/4])[0]
		self.offset += DEFAULTSIZE / 4
		
	def pprint(self):
		print "VorbisType1 type = 0x%02x" % self.type
		print "VorbisType1 codec = %s" % self.codec
		print "VorbisType1 vorbis_version = 0x%08x" % self.vorbis_version
		print "VorbisType1 audio_channels = 0x%02x -> %d" % (self.audio_channels, self.audio_channels)
		print "VorbisType1 audio_sample_rate = 0x%08x -> %d" % (self.audio_sample_rate, self.audio_sample_rate)
		print "VorbisType1 bitrate_max = 0x%08x -> %d" % (self.bitrate_max, self.bitrate_max)
		print "VorbisType1 bitrate_nom = 0x%08x -> %d" % (self.bitrate_nom, self.bitrate_nom)
		print "VorbisType1 bitrate_min = 0x%08x -> %d" % (self.bitrate_min, self.bitrate_min)
		print "VorbisType1 blocksize_0 = %s -> %d" % (bin(self.blocksize_0).zfill(4)[2:], self.blocksize_0)
		print "VorbisType1 blocksize_1 = %s -> %d" % (bin(self.blocksize_1).zfill(4)[2:], self.blocksize_1)
		print "VorbisType1 framing_flag = 0x%02x" % self.framing_flag

class VorbisType3:
	def __init__(self, data):
		self.offset = 0
		self.data = data

		self.type = struct.unpack("B", data[self.offset])
		self.offset += DEFAULTSIZE / 4

		self.codec = struct.unpack("6s", data[self.offset:self.offset + (DEFAULTSIZE / 4) * 6])
		self.offset += (DEFAULTSIZE / 4) * 6

		self.vendor_length = struct.unpack("<I", data[self.offset:self.offset+DEFAULTSIZE])[0]
		self.offset += DEFAULTSIZE

		self.vendor = struct.unpack("%ds" % self.vendor_length, data[self.offset:self.offset+self.vendor_length])[0]
		self.offset += self.vendor_length

		self.comment_list_length = struct.unpack("<I", data[self.offset:self.offset+DEFAULTSIZE])[0]
		self.offset += DEFAULTSIZE

		self.comment_length = []
		self.comment_list = []
		for i in range(0, self.comment_list_length):
			sz = struct.unpack("<I", data[self.offset:self.offset+DEFAULTSIZE])[0]
			self.offset += DEFAULTSIZE
			cmt = struct.unpack("%ds" % sz, data[self.offset:self.offset+sz])[0]
			self.offset += sz
			self.comment_length.append(sz)
			self.comment_list.append(cmt)

		self.framing_flag = struct.unpack("B", data[self.offset:self.offset + DEFAULTSIZE/4])[0]
		self.offset += DEFAULTSIZE / 4
		
	def pprint(self):
		print "VorbisType3 type = 0x%02x" % self.type
		print "VorbisType3 codec = %s" % self.codec
		print "VorbisType3 vendor_length = 0x%08x -> %d" % (self.vendor_length, self.vendor_length)
		print "VorbisType3 vendor = %s" % self.vendor
		print "VorbisType3 comment_list_length = 0x%08x -> %d" % (self.comment_list_length, self.comment_list_length)
		for i in range(0, self.comment_list_length):
			print "VorbisType3 comment_length[%d] = 0x%08x -> %d" % (i, self.comment_length[i], self.comment_length[i])
			print "VorbisType3 comment_list[%d] = %s" % (i, self.comment_list[i])
		print "VorbisType3 framing_flag = 0x%02x" % self.framing_flag

class VorbisType5:
	def __init__(self, data):
		self.offset = 0
		self.bits_used = 0
		self.quantvals = 0
		self.data = data
		self.bitstream = []
		self.r = OggReference(self.data)
		self.b = OggpackBuffer()
		self.s = Codebook()

		#print "data = ", len(data)
		#print "bits left in bitstream = ", len(data) * 8
		self.oggpack_readinit()
		
		print "sync pattern %06x" % self.oggpack_read(24, "sync pattern")
		self.s.dim = self.oggpack_read(16, "dimensions")
		print "s->dim ", self.s.dim
		self.s.dec_buf = [0] * (4 * self.s.dim)
		print "s->dec_buf", self.s.dec_buf
		self.s.entries = self.oggpack_read(24, "entries")
		print "s->entries ", self.s.entries
		self.ordered = self.oggpack_read(1, "ordered")
		print "ordered ", self.ordered
		if self.ordered == 0:
			self.lengthlist = [0] * self.s.entries
			self.sparse = self.oggpack_read(1, "sparse")
			print "allocate and unused entries (sparse) ", self.sparse
			if self.sparse == 0:
				#all entries used; no tagging
				self.s.used_entries = self.s.entries
				for i in range(0, self.s.entries):
					self.lengthlist[i] = self.oggpack_read(5, "lengthlist(%d)" % (i))+1
					if (self.lengthlist[i] + 1) > self.s.dec_maxlength:
						self.s.dec_maxlength = self.lengthlist[i] + 1
			else:#last vcb packet in file
				raise Exception("FML1!!!")
			print "lengthlist ", self.lengthlist
			print "s->used_entries ", self.s.used_entries
			print "s->dec_maxlength ", self.s.dec_maxlength
		else:
			raise Exception("FML2!!!")
		self.maptype = self.oggpack_read(4, "maptype")
		print "maptype ", self.maptype
		if self.maptype == 0:
			self.s.dec_nodeb = self.determine_node_bytes(self.s.used_entries, self.ilog(self.s.entries)/8+1);
			print "s->dec_nodeb ", self.s.dec_nodeb
			self.s.dec_leafw = self.determine_leaf_words(self.s.dec_nodeb, self.ilog(self.s.entries)/8+1)
			print "s->dec_leafw ", self.s.dec_leafw
			self.s.dec_type=0
			print "s->dec_type", self.s.dec_type
			#self.s.pprint()
			ret = self.make_decode_table(self.s, self.lengthlist, self.quantvals, self.maptype)
			print "make_decode_table returned ", ret
		else:
			raise Exception("FML3!!!!")

	def decpack(self, entry, used_entry, quantvals, b, maptype):
		ret=0;
	  	if b.dec_type == 0:
			print "\tentry", entry
			return entry
		if b.dec_type == 1:
			if(maptype==1):
				#vals are already read into temporary column vector here 
				for j in range(0, b.dim):
					off=entry%quantvals
					entry/=quantvals
					ret|=b.q_val[off]<<(b.q_bits*j)
			else:
				for j in range(0, b.dim):
					ret|=self.oggpack_read(b.q_bits)<<(b.q_bits*j)
			raise Exception("decpack unknown 1")
			return ret
		if b.dec_type == 2:
			for j in range(0, b.dim):
				off=entry%quantvals
				entry/=quantvals
				ret|=off<<(b.q_pack*j)
			raise Exception("decpack unknown 2")
			return ret

		if b.dec_type == 3:
			raise Exception("decpack unknown 3")
			return used_entry
		raise Exception("decpack unknown 4")
		return 0

	def make_words(self, l, n, r, quantvals, b, maptype):
#we fuck up here
#modify oggpack_read so that we print the buffer and offset
# given a list of word lengths, number of used entries, and byte width of a leaf, generate the decode table 
# static int _make_words(char *l,long n,ogg_uint32_t *r,long quantvals, codebook *b, oggpack_buffer *opb,int maptype){
#	ret = self.make_words(lengthlist, s.entries, work, quantvals, s, maptype)
#quantvals = 0, maptype = 0, l = n * 2, n = 32, work = n*2+1
		print l, n, r, quantvals, b, maptype
#		for i in range(0, len(l)):
#			self.oggpack_read(l[i]<<2, "lengthlist[%d]%d<<2 = %d" %(i, l[i], l[i]<<2))
#		return
		marker = [0] * 33
		top = 0
		count=0
		print "n", n
		if (n<1):
			#print "if (n<1):"
			return 1
		if (n<2):
			r[0] = 0x80000000
		else:
			for i in range(0, n):
				length = l[i]
				print "length = ", length
				if (length):
					entry = marker[length]
					chase = 0
					print "entry = ", entry
					for j in range(0, length-1):
						#print "j, length-1", j, length-1
						bit=(entry>>(length-j-1))&1
						print "bit", bit
						if(chase >= top):
							if (chase < 0 or chase >= n):
								#print "if (chase < 0 or chase >= n):"
								return 1
							top += 1
							r[chase*2] = top
							#print "top", top
							r[chase*2+1] = 0
						else:
							if (chase < 0 or chase >= n or chase*2+bit > n*2+1):
								#print "if (chase < 0 or chase >= n or chase*2+bit > n*2+1)"
								return 1
							if( not r[chase*2+bit]):
								r[chase*2+bit] = top
							#print "chase", chase, "r", r, "bit", bit 
							chase=r[chase*2+bit]
							#print "chase=r[chase*2+bit]", chase
							if (chase < 0 or chase >= n):
								print "if (chase < 0 or chase >= n):", chase, n
								return 1
						#scope change hax
						#print "entry", entry
						#print "length", length
						#print "j", j
						bbit=(entry>>(length-j-1))&1;
						if(chase>=top):
							top+=1
							r[chase*2+1]=0
						count+=1
						#fail here
						print "bbit = ", bbit
						r[chase*2+bbit]= self.decpack(i,count,quantvals,b,maptype) | 0x80000000
						#end
					#Look to see if the next shorter marker points to the node above. if so, update it and repeat.
					for j in range(length, 0, -1):
						if(marker[j]&1):
							marker[j]=marker[j-1]<<1
							break
						marker[j]+=1
					for j in range(length+1, 33):
						if((marker[j]>>1) == entry):
							entry=marker[j]
							marker[j]=marker[j-1]<<1
						else:
							break
		return 0

	def make_decode_table(self, s, lengthlist, quantvals, maptype):
		i = 0
		if not lengthlist:
			raise Exception("NO lengthlist")
		if s.dec_nodeb == 4:
			raise Exception("NOT IMPLEMENTED")
#		if (s.used_entries > INT_MAX/2 || s->used_entries*2 > INT_MAX/((long) sizeof(*work)) - 1) return 1;
#		/* Overallocate as above */
#		work=alloca((s->entries*2+1)*sizeof(*work));
		work = [0] * (s.entries * 2 + 1)
		ret = self.make_words(lengthlist, s.entries, work, quantvals, s, maptype)
#		print "make_words returned ", ret
#		if(_make_words(lengthlist,s->entries,work,quantvals,s,opb,maptype))return 1;
#		if (s->used_entries > INT_MAX/(s->dec_leafw+1)) return 1;
#		if (s->dec_nodeb && s->used_entries * (s->dec_leafw+1) > INT_MAX/s->dec_nodeb) return 1;
#		s->dec_table=_ogg_malloc((s->used_entries*(s->dec_leafw+1)-2)* s->dec_nodeb);
#		if (!s->dec_table) return 1;
		#return 1

		#s.pprint()

	def determine_leaf_words(self, nodeb, leafwidth):
		if(leafwidth > nodeb):
			return 2
		return 1

	def determine_node_bytes(self, used, leafwidth):
		#special case small books to size 4 to avoid multiple special cases in repack
		if(used<2):
			return 4
		if(leafwidth==3):
			leafwidth=4
		if(self.ilog(3*used-6)+1 <= leafwidth*4):
			if (leafwidth/2):
				return leafwidth/2
			else:
				return 1
		return leafwidth

	def ilog(self, v):
		ret=0
		while(v):
			ret += 1
			v >>= 1
		return ret

	def oggpack_readinit(self):
		self.b.tail = self.r
		self.b.head = self.r
		self.b.count = 0

		if self.b.head.length > 0:
			self.b.headptr = self.b.head.buffer.data[self.b.head.begin:]
			self.b.headend = self.b.head.length
		else:
			self.b.headptr = 0
			self.b.headend = 0
		self.b.count = self.b.head.length
		#idk wtf this should be right now
		self.b.headbit = 0

	def oggpack_read(self, bits, log = None):
		ret=self.oggpack_look(bits, log)
		self.oggpack_adv(bits);
		return ret

	def oggpack_adv(self, bits):
		bits += self.b.headbit
		self.b.headbit = bits & 7 
		self.b.headend -= (bits >> 3)
		self.b.headptr = self.b.headptr[(bits >> 3):]

	def oggpack_look(self, bits, log = None):
		global MASK
		m = MASK[bits]
		ret = 0
		BITS = bits
		bits += self.b.headbit
		ret = ord(self.b.headptr[0]) >> self.b.headbit
		if (bits > 8):
			ret |= ord(self.b.headptr[1]) << (8 - self.b.headbit)
			if (bits > 16):
				ret |= ord(self.b.headptr[2]) << (16 - self.b.headbit)
				if (bits > 24):
					ret |= ord(self.b.headptr[3]) << (24 - self.b.headbit)
					if (bits > 32 and self.b.headbit):
						ret |= ord(self.b.headptr[4]) << (32 - self.b.headbit)
		ret &= m
		if log:
			print "log:", log
			print "bits :", bits
			print "returns ", ret
			print binascii.hexlify(self.b.headptr)
			print ""
		return ret

	def pprint(self):
		print "VorbisType5 "#sync_pattern = 0x%06x" % self.sync_pattern


class OggPage:
	def __init__(self, data, offset, page_num, vcb):
		self.page_num = page_num
		self.offset = offset
		self.capture_pattern = binascii.hexlify(data[offset : offset + DEFAULTSIZE])
		self.toffset = self.offset + DEFAULTSIZE

		self.version = struct.unpack( "B", data[self.toffset])[0]
		self.toffset += DEFAULTSIZE / 4

		self.header_type = struct.unpack( "B", data[self.toffset])[0]
		self.toffset += DEFAULTSIZE / 4

		self.gpos_high = struct.unpack("<I", data[self.toffset:self.toffset+DEFAULTSIZE])[0]
		self.toffset += DEFAULTSIZE

		self.gpos_low = struct.unpack("<I", data[self.toffset:self.toffset+DEFAULTSIZE])[0]
		self.toffset += DEFAULTSIZE

		self.bitstream_serial_num = struct.unpack("<I", data[self.toffset:self.toffset+DEFAULTSIZE])[0]
		self.toffset += DEFAULTSIZE

		self.page_sequence = struct.unpack("<I", data[self.toffset:self.toffset+DEFAULTSIZE])[0]
		self.toffset += DEFAULTSIZE

		self.checksum = struct.unpack("<I", data[self.toffset:self.toffset+DEFAULTSIZE])[0]
		self.toffset += DEFAULTSIZE

		self.page_segments = struct.unpack( "B", data[self.toffset])[0]
		self.toffset += DEFAULTSIZE / 4

		#page_segments is the number of bytes to follow... each byte is a size of a segment
		self.segment_table =  struct.unpack("%dB" % self.page_segments, data[self.toffset : self.toffset + self.page_segments])

		self.toffset += (DEFAULTSIZE / 4) * self.page_segments
		self.v_segment = []
		self.segment = []
		for i in range(0, len(self.segment_table)):
			#each one of these are the data for the decoder
			self.segment.append(binascii.hexlify(data[self.toffset : self.toffset + self.segment_table[i]]))
			if self.page_num == 0:
				vcb.type1 += data[self.toffset : self.toffset + self.segment_table[i]]
			elif self.page_num == 1:
				vcb.type3 += data[self.toffset : self.toffset + self.segment_table[i]]
			else:
				vcb.type5.append(data[self.toffset : self.toffset + self.segment_table[i]])
			self.toffset += self.segment_table[i]
		self.page_length = self.toffset - self.offset

	def pprint(self):
		print "OggPage_header(%d) @ offset 0x%08x" % (self.page_num, self.offset)
		print "{"
		print "uint32 capture_pattern = 0x%08x"  % int(self.capture_pattern, 16)
		print "byte version = 0x%02x -> %d" % (self.version, self.version)
		print "byte header_type = 0x%02x -> %d" % (self.header_type, self.header_type)
		print "uint64 granule_position = 0x%08x 0x%08x" % (self.gpos_high, self.gpos_low)
		print "uint32 bitstream_serial_num = 0x%08x -> %d" % (self.bitstream_serial_num, self.bitstream_serial_num)
		print "uint32 page_sequence = 0x%08x -> %d" % (self.page_sequence, self.page_sequence)
		print "uint32 checksum = 0x%08x -> %d" % (self.checksum, self.checksum)
		print "byte page_segments = 0x%02x -> %d" % (self.page_segments, self.page_segments)
		print "byte[%d] segment_table = " % (self.page_segments-1), self.segment_table
		for i in range(0, len(self.segment_table)):
			print "byte[%d] segment(%d) =" % (self.segment_table[i]-1, i), self.segment[i]
			#self.v_segment[i].pprint()
			print ""
		print "} size = %08x" % self.page_length
		print ""


def split_byte(byte):
	bits = bin(byte)[2:].zfill(8)
	h = bits[0:4]
	l = bits[4:]
	return [int(h, 2), int(l, 2)]


def parse_ogg(data):
	offset = 0x00000000
	page_num = 0
	magic = binascii.hexlify(data[offset : offset + DEFAULTSIZE])
	vcb = Vorbis()
	while (int(magic, 16) == OGGMAGIC):
		ogg = OggPage(data, offset, page_num, vcb)
		#ogg.pprint()
		offset = ogg.toffset
		magic = binascii.hexlify(data[offset : offset + DEFAULTSIZE])
		page_num += 1
		if not magic:
			print "EOF!!?!"
			break

	#vcb.pprint()
	#t1 = VorbisType1(vcb.type1)
	#t1.pprint()
	#
	#t3 = VorbisType3(vcb.type3)
	#t3.pprint()
	
	crap = re.split("(\x42\x43\x56)", "".join(vcb.type5))
	tmp = []
	for i in range(1, len(crap), 2):
		tmp.append(crap[i]+crap[i+1])
	vcb.type5 = tmp
#	for i in range(0, len(vcb.type5)):
#		t5 = VorbisType5(vcb.type5[i])
#		t5.pprint()
#		print ""
	t5 = VorbisType5(vcb.type5[1])
	t5.pprint()
	print ""



	
def get_data(file_name):
	fd = open(file_name, "rb")
	data = fd.read()
	fd.close()
	parse_ogg(data)

def usage():
	print "%s file" % sys.argv[0]
	sys.exit(0)

def main():
	data = get_data(sys.argv[1])


if __name__ == '__main__':
	if len(sys.argv) < 2:
		usage()
	if not os.path.exists(sys.argv[1]):
		usage()
	main()



