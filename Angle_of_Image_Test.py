
import numpy as np
import librosa
import librosa.display
from matplotlib import pyplot as plt

filename = "./sounds/stereo_piano.wav"  # path to audio source

# Audio sample is pan'ed 40 to the LEFT = left side signal should be stronger

y, sr = librosa.load(filename, mono=False)

# The Fourier transforms of both channels
L = np.abs(librosa.stft(y[0], hop_length=512))
R = np.abs(librosa.stft(y[1], hop_length=512))

# Both channels translated to the signal strength in dB
LA = librosa.amplitude_to_db(L, ref=np.max)
RA = librosa.amplitude_to_db(R, ref=np.max)

# Now angles:

Q = ((LA - RA)/(LA + RA))/np.sin(30)
print("Q er arcsin:")
# print(Q)

for i in Q:
    print(i)

fig, ax = plt.subplots()
ax.set_xlim(-90, 90)
ax.set_ylim(0, 20000)
ax.set(title='Stereo Image')
ax.set_xlabel('Angle of stereo image')
ax.set_ylabel('Frequency in Hz')
ax.label_outer()
plt.axvline(x=0, color='b', linestyle='-')

# MISSING: to plot the data from Q in the figure.

plt.show()
