
//#define _WIN32_WINNT 0x500
//#include <windows.h>
#include <stdio.h>
#include <string.h>
//#include <winbase.h>

#define InSafeArea(p, head, length) (p >= head && p <(head+length))

__declspec (dllexport)
ssize_t Predict(const size_t row_length,
  const size_t rows, unsigned char *pixels) //,
  //const size_t number_dst_pixels, unsigned char *dst)
{
	unsigned char *p = pixels;
	int len;
	int counts = rows;
	
	int length = row_length*rows;
	
	while(counts)
	{
		len = row_length;
		p += row_length-1;
		while(--len)
		{
			//if (!InSafeArea(p, pixels, length)) {
			//	printf("!!%d", p-pixels);
			//}
			*p-- -= *(p-1);
			
			//if (!InSafeArea(p, pixels, length)) {
			//	printf("!!%d", p-pixels);
			//}
		}
		
		p += row_length;
		counts--;
	}
		
	/*
	for y in range(rows):
		for x in range(row_length-1, 0, -1):
			b = bdata[y*row_length+x] - bdata[y*row_length+x-1]
			if b < 0: b += 256
			bdata[y*row_length+x] = b
	*/
	//printf("???\n");
	return 0;

}

__declspec (dllexport)
ssize_t Depredict(const size_t row_length,
  const size_t rows, unsigned char *pixels)
{
	unsigned char *p = pixels;
	int len;
	int counts = rows;
	
	while(counts)
	{
		len = row_length;
		while(--len)
		{
			*(p+1) += *p++;
		}
		p++;
		counts--;
	}
		
	/*
	for y in range(rows):
		for x in range(0, row_length-1):
			b = bdata[y*row_length+x+1] + bdata[y*row_length+x]
			if b > 255: b -= 256
			bdata[y*row_length+x+1] = b
	*/
	return 0;

}

// 修正了 length < 128 時, packets卻沒有減少的Bug
// 但是還未實做各種 depth
__declspec (dllexport)
ssize_t MyDecodePSDPixels(const size_t number_compact_pixels,
  const unsigned char *compact_pixels,const ssize_t depth,
  const size_t number_pixels,unsigned char *pixels)
{
  register ssize_t i, j;
  unsigned char pixel;
  unsigned char length;
  ssize_t packets;
  packets=(ssize_t) number_compact_pixels;
  for (i=0; (packets > 1) && (i < (ssize_t) number_pixels); )
  {
    length=(*compact_pixels++);
    packets--;
    if (length == 128)
      continue;
	if (length > 128)
    {
	  length=256-length+1;
	  pixel=(*compact_pixels++);
	  packets--;
	  for (j=0; j < (ssize_t) length; j++)
      {
	    *pixels++=(unsigned char) pixel;
        i++;
	  }
	  continue;
	}
	length++;
	for (j=0; j < (ssize_t) length; j++)
    {
	  *pixels++=(*compact_pixels);
      i++;
	  compact_pixels++;
	  packets--;
	  if (packets == 0)
	    return(i);
	}
	
  }
  return(i);
}


__declspec (dllexport)
ssize_t DecodePSDPixels(const size_t number_compact_pixels,
  const unsigned char *compact_pixels,const ssize_t depth,
  const size_t number_pixels,unsigned char *pixels)
{
  int
    pixel;

  register ssize_t
    i,
    j;

  ssize_t
    packets;

  size_t
    length;

  packets=(ssize_t) number_compact_pixels;
  for (i=0; (packets > 1) && (i < (ssize_t) number_pixels); )
  {
    length=(*compact_pixels++);
    packets--;
    if (length == 128)
      continue;
    if (length > 128)
      {
        length=256-length+1;
        pixel=(*compact_pixels++);
        packets--;
        for (j=0; j < (ssize_t) length; j++)
        {
          switch (depth)
          {
            case 1:
            {
              *pixels++=(pixel >> 7) & 0x01 ? 0U : 255U;
              *pixels++=(pixel >> 6) & 0x01 ? 0U : 255U;
              *pixels++=(pixel >> 5) & 0x01 ? 0U : 255U;
              *pixels++=(pixel >> 4) & 0x01 ? 0U : 255U;
              *pixels++=(pixel >> 3) & 0x01 ? 0U : 255U;
              *pixels++=(pixel >> 2) & 0x01 ? 0U : 255U;
              *pixels++=(pixel >> 1) & 0x01 ? 0U : 255U;
              *pixels++=(pixel >> 0) & 0x01 ? 0U : 255U;
              i+=8;
              break;
            }
            case 4:
            {
              *pixels++=(unsigned char) ((pixel >> 4) & 0xff);
              *pixels++=(unsigned char) ((pixel & 0x0f) & 0xff);
              i+=2;
              break;
            }
            case 2:
            {
              *pixels++=(unsigned char) ((pixel >> 6) & 0x03);
              *pixels++=(unsigned char) ((pixel >> 4) & 0x03);
              *pixels++=(unsigned char) ((pixel >> 2) & 0x03);
              *pixels++=(unsigned char) ((pixel & 0x03) & 0x03);
              i+=4;
              break;
            }
            default:
            {
              *pixels++=(unsigned char) pixel;
              i++;
              break;
            }
          }
        }
        continue;
      }
    length++;
    for (j=0; j < (ssize_t) length; j++)
    {
      switch (depth)
      {
        case 1:
        {
          *pixels++=(*compact_pixels >> 7) & 0x01 ? 0U : 255U;
          *pixels++=(*compact_pixels >> 6) & 0x01 ? 0U : 255U;
          *pixels++=(*compact_pixels >> 5) & 0x01 ? 0U : 255U;
          *pixels++=(*compact_pixels >> 4) & 0x01 ? 0U : 255U;
          *pixels++=(*compact_pixels >> 3) & 0x01 ? 0U : 255U;
          *pixels++=(*compact_pixels >> 2) & 0x01 ? 0U : 255U;
          *pixels++=(*compact_pixels >> 1) & 0x01 ? 0U : 255U;
          *pixels++=(*compact_pixels >> 0) & 0x01 ? 0U : 255U;
          i+=8;
          break;
        }
        case 4:
        {
          *pixels++=(*compact_pixels >> 4) & 0xff;
          *pixels++=(*compact_pixels & 0x0f) & 0xff;
          i+=2;
          break;
        }
        case 2:
        {
          *pixels++=(*compact_pixels >> 6) & 0x03;
          *pixels++=(*compact_pixels >> 4) & 0x03;
          *pixels++=(*compact_pixels >> 2) & 0x03;
          *pixels++=(*compact_pixels & 0x03) & 0x03;
          i+=4;
          break;
        }
        default:
        {
          *pixels++=(*compact_pixels);
          i++;
          break;
        }
      }
      compact_pixels++;
    }
  }
  return(i);
}


#define endian_swap_u16(x) x = ((x>>8) | (x<<8))

__declspec (dllexport)
ssize_t MyEncodePSDPixels2(const size_t number_pixels,
  const unsigned char *pixels,const ssize_t depth, const size_t row_length,
  const size_t scan_lines, unsigned short *byte_counts,
  const size_t number_compact_pixels,unsigned char *compact_pixels)
{
	const unsigned char *src=pixels;
	const unsigned char *run, *dataend, *p;
	
	unsigned char *dst=compact_pixels;
	unsigned char *q;
	
	int i, count, maxrun;
	ssize_t n;
	unsigned int packets;
	unsigned short row_packets;
	
	
	//n = number_pixels;
	packets = 0;
	
	// Each row  must be packed separately. 
	// Do not compress across row boundaries.
	for( i=0, q = dst; i<number_pixels/row_length; i++)
	{
		row_packets = 0;
		n = row_length;
		dataend = src + row_length;
		for( run = src;
			 n > 0 && p != dataend;
			 run = p, n -= count 
		) {
			// A run cannot be longer than 128 bytes.
			maxrun = n < 128 ? n : 128;
			if(run <= (dataend-3) && run[1] == run[0] && run[2] == run[0]){
				// 'run' points to at least three duplicated values.
				// Step forward until run length limit, end of input,
				// or a non matching byte:
				for( p = run+3; p < (run+maxrun) && *p == run[0]; )
					++p;
				count = p - run;
				// replace this run in output with two bytes:
				row_packets += 2;
				packets += 2;
				if (packets > number_compact_pixels) return -1; //return packets-2;
				*q++ = 1+256-count; /* flag byte, which encodes count (129..254) */
				*q++ = run[0];      /* byte value that is duplicated */
				
			} else {
				// If the input doesn't begin with at least 3 duplicated values,
				// then copy the input block, up to the run length limit,
				// end of input, or until we see three duplicated values:
				for( p = run; p < (run+maxrun); )
					if(p <= (dataend-3) && p[1] == p[0] && p[2] == p[0])
						break; // 3 bytes repeated end verbatim run
					else
						++p;
				count = p - run;
				row_packets += count+1;
				packets += count+1;
				if (packets > number_compact_pixels) return -1; //return packets-count-1;
				*q++ = count-1;        /* flag byte, which encodes count (0..127) */
				memcpy(q, run, count); /* followed by the bytes in the run */
				q += count;
			}
		}
		byte_counts[i] = endian_swap_u16(row_packets);
		src = dataend;
		
	}
	
	//printf("%d, %d", q - dst, packets);
	if ((unsigned int)(q - dst) == packets) {
		return q - dst;
	} else {
		return 0;
	}
}


__declspec (dllexport)
ssize_t MyEncodePSDPixels(const size_t number_pixels,
  const unsigned char *pixels,const ssize_t depth, //const size_t row_length,
  const size_t number_compact_pixels,unsigned char *compact_pixels)
{
	const unsigned char *src=pixels;
	const unsigned char *run, *dataend, *p;
	
	unsigned char *dst=compact_pixels;
	unsigned char *q;
	
	int i, count, maxrun;
	ssize_t n;
	unsigned int packets;
	
	
	
	n = number_pixels;
	packets = 0;
	
	//for(i=0; i<number_pixels/row_length; i++)
	//{
		dataend = src + n;
		for( run = src, q = dst;
			 n > 0 && p != dataend;
			 run = p, n -= count 
		) {
			// A run cannot be longer than 128 bytes.
			maxrun = n < 128 ? n : 128;
			if(run <= (dataend-3) && run[1] == run[0] && run[2] == run[0]){
				// 'run' points to at least three duplicated values.
				// Step forward until run length limit, end of input,
				// or a non matching byte:
				for( p = run+3; p < (run+maxrun) && *p == run[0]; )
					++p;
				count = p - run;
				// replace this run in output with two bytes:
				packets += 2;
				if (packets > number_compact_pixels) return -1; //return packets-2;
				*q++ = 1+256-count; /* flag byte, which encodes count (129..254) */
				*q++ = run[0];      /* byte value that is duplicated */
				
			} else {
				// If the input doesn't begin with at least 3 duplicated values,
				// then copy the input block, up to the run length limit,
				// end of input, or until we see three duplicated values:
				for( p = run; p < (run+maxrun); )
					if(p <= (dataend-3) && p[1] == p[0] && p[2] == p[0])
						break; // 3 bytes repeated end verbatim run
					else
						++p;
				count = p - run;
				packets += count+1;
				if (packets > number_compact_pixels) return -1; //return packets-count-1;
				*q++ = count-1;        /* flag byte, which encodes count (0..127) */
				memcpy(q, run, count); /* followed by the bytes in the run */
				q += count;
			}
		}
	//}
	
	//printf("%d, %d", q - dst, packets);
	if ((unsigned int)(q - dst) == packets) {
		return q - dst;
	} else {
		return 0;
	}
}

// Assuming compressor logic is maximally efficient,
// worst case input with no duplicate runs of 3 or more bytes
// will be compressed into a series of verbatim runs no longer
// than 128 bytes, each preceded by length byte.
// i.e. worst case output length is not more than 129*ceil(n/128)
// or slightly tighter, 129*floor(n/128) + 1 + (n%128)

ssize_t packbits(unsigned char *src, unsigned char *dst, ssize_t n){
	unsigned char *p, *q, *run, *dataend;
	int count, maxrun;

	dataend = src + n;
	for( run = src, q = dst; n > 0; run = p, n -= count ){
		// A run cannot be longer than 128 bytes.
		maxrun = n < 128 ? n : 128;
		if(run <= (dataend-3) && run[1] == run[0] && run[2] == run[0]){
			// 'run' points to at least three duplicated values.
			// Step forward until run length limit, end of input,
			// or a non matching byte:
			for( p = run+3; p < (run+maxrun) && *p == run[0]; )
				++p;
			count = p - run;
			// replace this run in output with two bytes:
			*q++ = 1+256-count; /* flag byte, which encodes count (129..254) */
			*q++ = run[0];      /* byte value that is duplicated */
		}else{
			// If the input doesn't begin with at least 3 duplicated values,
			// then copy the input block, up to the run length limit,
			// end of input, or until we see three duplicated values:
			for( p = run; p < (run+maxrun); )
				if(p <= (dataend-3) && p[1] == p[0] && p[2] == p[0])
					break; // 3 bytes repeated end verbatim run
				else
					++p;
			count = p - run;
			*q++ = count-1;        /* flag byte, which encodes count (0..127) */
			memcpy(q, run, count); /* followed by the bytes in the run */
			q += count;
		}
	}
	return q - dst;
}
