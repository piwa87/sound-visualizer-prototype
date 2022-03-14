import librosa
import librosa.display
from playsound import playsound
import matplotlib.pyplot as plt
import numpy as np

print('')
print('     WELCOME TO STEREO CHANNEL SOUND VISULIZER   \n')
print('     Choose sound to visualize: ')
print('     [1]: Grand piano')
print('     [2]: Synth')
print('     [3]: Synth with auto pan')
print('')

soundChoice = input()
optionInt = int(soundChoice)

print('     Choose scale: ')
print('     [1]: Logarithmic')
print('     [2]: Linear\n')

scaleChoice = input()
if int(scaleChoice) == 1:
    scale = 'log'
else:
    scale = 'linear'

play = input('     Play the sound sample before visualizing? (y/n) ')


def chooseSound(x):
    return {
        1: ('./sounds/stereo_piano.wav', 'Grand piano (45 right pan'),
        2: ('./sounds/stereo_synth.wav', 'Synth (max. 64 left pan)'),
        3: ('./sounds/stereo_synth_pan.wav', 'Synth with changing pan from left to right'),
    }[x]


(filePath, title) = chooseSound(optionInt)

# Loading the audio data & sample rate
y, sr = librosa.load(filePath, mono=False)

# Create dB-scaled spectograms for left & right channel
L = librosa.amplitude_to_db(np.abs(librosa.stft(y[0])), ref=np.max)
R = librosa.amplitude_to_db(np.abs(librosa.stft(y[1])), ref=np.max)

# Figure 1 (Left channel):
fig, ax = plt.subplots(nrows=2, ncols=1, sharex=True)

img = librosa.display.specshow(L, y_axis=scale, x_axis='time', sr=sr, ax=ax[0])
ax[0].set(title='Left Channel | ' + title)
ax[0].label_outer()

# Figure 2 (Right channel):
img2 = librosa.display.specshow(R, y_axis=scale, x_axis='time', ax=ax[1])
ax[1].set(title='Right Channel | ' + title)
ax[1].label_outer()

fig.colorbar(img, ax=ax, format="%+2.f dB")

# Play the sound if asked for
if play == 'y':
    playsound(filePath)

# Show the graphics
plt.show()
