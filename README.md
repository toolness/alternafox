Alternafox is a command-line Python script for OS X that makes it possible to use [Aurora][] and [Nightly][] as entirely separate browsers from Firefox itself.

This means, for example, that you can use Firefox for work, Aurora for personal, and Nightly for development. Each browser uses its own separate profile, so you can install different add-ons and personas in each, and run them all at the same time.

These browsers are fully compatible with [Choosy][].

## Usage

1. Download the [update_alternafox.py][] script to your desktop.

2. Open Terminal and run the following commands:

        cd ~/Desktop
        python update_alternafox.py aurora
    
The above command will automatically download and install the latest version of Aurora as a separate browser in `/Applications/Aurora.app`. If you'd like to also get Nightly, run:

    python update_alternafox.py nightly
    
That browser will be installed in `/Applications/Nightly.app`.

You can also run the script to update your installation of Aurora and/or Nightly.

[update_alternafox.py]: https://github.com/toolness/alternafox/raw/master/update_alternafox.py

## Technical Details

The script makes a simple modification to the `application.ini` file in Aurora and Nightly, which has a side effect of disabling updates. You can update your browsers by running the Alternafox command-line script, however.

Note that this script is completely unsupported by Mozilla and is not guaranteed to work. It's quite a hack, and your computer might explode.

Aurora profile data will be stored in `~/Library/Application Support/Aurora/` and Nightly profile data will be in `~/Library/Application Support/Nightly/`.

## Similar Projects

Also see [Fireskulk][].

[Aurora]: http://www.mozilla.com/en-US/firefox/channel/
[Nightly]: http://nightly.mozilla.org/
[Choosy]: http://www.choosyosx.com/
[Fireskulk]: https://github.com/toolness/fireskulk
