# analyze trips

import numpy as np
import pickle
import matplotlib.pyplot as plt
from scipy.stats import skew


# load trips
trips = pickle.load(open('data/trips.pkl', 'rb'))

# all curb to gate times
c2g = [trip.curb_to_gate/60 for trip in trips]
sample = len(trips)
mean = np.mean(c2g)
std = np.std(c2g)
median = np.median(c2g)
quart1 = np.percentile(c2g, 25)
quart3 = np.percentile(c2g, 75)
skw = skew(c2g)

print('sample:', sample)
print('mean:', mean)
print('std:', std)
print('median:', median)
print('1st quartile:', quart1)
print('3rd quartile:', quart3)
print('skew:', skw)
print('min:', min(c2g))
print('max:', max(c2g))

plt.figure(figsize=(8,6))
plt.hist(c2g, bins=238)
plt.title('Distribution of Curb to Gate Times   N=%s' % sample, fontsize=16)
plt.xlabel('Curb to Gate Time (Minutes)')
plt.ylabel('Count')
plt.tight_layout()
plt.savefig('figures/c2g_dist.png', dpi=300)

bins = list(range(0, 241))
bin_counts = {str(b): 0 for b in bins}
for c in c2g:
	bin_counts[str(int(c))] += 1
for key, value in bin_counts.items():
	print(key, value)
