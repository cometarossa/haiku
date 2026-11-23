# app_server correctness probe (AI-assisted independent fork)

The standalone window_lifecycle.cpp uses native Haiku BApplication,
BWindow and the Be API to create and then close many GUI windows in
batches, with 1..16 simultaneous window loopers per batch.

Build and run inside Haiku (not on the macOS host):

    g++ -std=c++11 -O2 -Wall -Wextra -o window_lifecycle \
      window_lifecycle.cpp -lbe
    ./window_lifecycle 10 10 > window_lifecycle.csv \
      2> window_lifecycle.stderr

The test asserts successful window locks and shutdown; it does not
measure frame rate, desktop responsiveness or bare-metal SMP speed.
The official beta6 reference must be tested first, before the future
fork-built image is used for regression comparison. No upstream
submissions of AI-assisted code.
