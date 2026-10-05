# RF Mixer Spur Calculator

## Inspiration

Marki Microwave is a company that makes RF Mixers, among other things. They
host an [online spur calculator](https://markimicrowave.com/technical-resources/tools/spur-calculator/)
on their website that computes mixer spur levels. It has proven very
useful, but one time, when I really needed it, their website went down. That
event was the motivation to make this python version.

## Spur Value Calculation

Calculating the values of mixer spur suppression is not possible (or at least,
not really possible) without knowledge of performance parameters of the mixer
itself. See reference "Predicting Intermodulation Suppression in
Double-Balanced Mixers" by Henderson for more information on that, a copy
of a PDF of the paper is included in this repository.

I don't know where Marki got their numbers from. I assume they are from some
sort of generalization of experimental data. By default I use spur values I
copied directly out of their tool since it is the most complete I can find
while remaining component agnostic, if not manufacturer agnostic.

Mixer manufacturers often include spur tables in the datasheet of any individual
product. If you have access to this sort of information, e.g. you want to
compute spurs you'll get from a part you have already chosen, I strongly
recommend modifying this script to use the true values of your part.

This script only computes the output spectra for single-tone input, with no
consideration for two-tone intermodulation products. This is because the
two-tone intermodulation is too hard.

## Visualization

This script generates two plots. The first is a faithful recreation of the
Marki tool, and the second is one I made up. They contain the same information.
