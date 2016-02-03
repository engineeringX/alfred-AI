import sys

f = open(sys.argv[1], 'r')

missed = 0
true_count = 0
count = int(f.readline().split(',')[6])
f.seek(0, 0)
lines = f.readlines()
for line in lines:
  id = int(line.split(',')[6])
  missed += (id - count)
  print id, count, missed
  true_count += 1
  if (id - count) == 0:
    count += 1
  else:
    count = id + 1

print 'missed: %d, count: %d' % (missed, true_count)
f.close()
