
import librosa
import librosa.display
from playsound import playsound
import matplotlib.pyplot as plt
import numpy as np

print('')
print('     WELCOME TO SINGLE CHANNEL SOUND VISULIZER   \n')
print('     Choose sound to visualize: ')
print('     [1]: Kick drum')
print('     [2]: Lead synthesizer')
print('     [3]: Groovy band with horns')
print('     [4]: Explosion')
print('     [5]: Rhythmic synthesizer with filter')
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
        1: ('./sounds/01_kick_drum.wav', 'Kick drum (2 last hits with reverb)'),
        2: ('./sounds/02_synth_eq.wav', 'Lead synthesizer with EQ'),
        3: ('./sounds/03_horns.wav', 'Groovy band with horns'),
        4: ('./sounds/04_explosion.wav', 'Explosion'),
        5: ('./sounds/05_synth_pad.wav', 'Rhytmic Synth Pad with a filter')
    }[x]


(filePath, title) = chooseSound(optionInt)

# Loading the audio data & sample rate
y, sr = librosa.load(filePath, mono=True)

# Apply Fourier transform and convert the amplitude spectogram to dB-scaled spectogram
D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)

# Building the graphical image
fig, ax = plt.subplots()

img = librosa.display.specshow(D, y_axis=scale, x_axis='time', sr=sr, ax=ax)
ax.set(title=title)
ax.set_xlabel('Time in seconds')
ax.label_outer()

fig.colorbar(img, ax=ax, format="%+2.f dB")

# Play the sound if asked for
if play == 'y':
    playsound(filePath)

# Show the graphics
plt.show()
