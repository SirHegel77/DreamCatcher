DreamCatcher
============

Experimental project for recording and analyzing sleep cycles using Raspberry Pi.

#Background

The purpose of this project is to test whether or not [sleep cycles](http://en.wikipedia.org/wiki/Sleep#Stages) of a sleeping individual can be detected using a MEMS IMU without previous experience on this subject. 

Sleep consists of multiple successive stages, which form a sleep cycle. During a regular night multiple sleep cycles are usually gone through. It is common to awake for a brief moment between sleep cycles especially near morning. Sleep stages can be divided into NREM and REM sleep, and dreams are usually experienced during REM sleep. During deep NREM sleep muscular activity is low and the body is very relaxed. On the other hand, during REM sleep brain activity is nearly as high as in awake state, which reflects in higher muscular activity as well.

I know that this information is used in real sleep research, so I decided to test whether I could see the changes in muscular activity during sleep cycles using a simple approach. I decided to put an accelerometer under my mattress for measuring my nightly movements. I wrote this simple program to record and plot the data.

The goal of this project is to see if sleep stages could be recognized in the accelerometer data. If the sleep stages can be visually detected from the graphs, it is interesting to see if sleep stages could be detected programmatically using an algorithm. Detected sleep stage could then perhaps be used eg. to trigger an audio or visual stimulus to induce [lucid dreaming](http://en.wikipedia.org/wiki/Lucid_dream).

I started this project just for fun, and I do not know yet what to expect from the result of this experiment. I wrote the code from scratch, so I may have re-invented the rectangular wheel, but at least this has been quite interesting so far.


## Materials used

[Current hardware](https://dl.dropboxusercontent.com/u/10487209/20140223_215414.jpg) consists of following items:

 * Raspberry Pi, obviously
 * [Pololu MinIMU-9 v2](http://www.pololu.com/product/1268)
 * [Adafruit RGB Negative LCD + Keypad](http://www.adafruit.com/products/1110)
 * Cables and other stuff as required
 
## Software used

* Fork from [minimu9-ahrs](https://github.com/SirHegel77/minimu9-ahrs.git)

I changed the original implementation simply by including timestamp in outupt just in case I might need id in analyzing the results.

* [NumPy + Matplotlib](http://wyolum.com/numpyscipymatplotlib-on-raspberry-pi/)

I decided to use NumPy in my project, as I might want to do FFT transform to analyze the results and to draw [fancy graphs](https://dl.dropboxusercontent.com/u/10487209/1392844852.png) from the output. 

* [Supervisord](http://supervisord.org/)

Supervisord is used to run DreamCatcher as background process.
