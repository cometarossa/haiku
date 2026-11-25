# V14 same-image first preflight pair
Fresh trial1 overlay, source 63cc5489, identical hashed 320x180 numbered
fixture. OFF produces ring-buffer allocation and connection failure,
then software retry; ON logs LAB_MEDIA_OVERLAY_PREFLIGHT software
format=8 and no overlay retry. Both players exit 0, each three active
position samples advancing. ON log also contains one Error sending
buffer; cause/phase not established, must be investigated.
First position 1.9s OFF / 2.9s ON is not a latency measurement:
one fixed-order pair, cold/warm cache and scripting overhead uncontrolled.
Marker cleanup and absence verified. Prior eight-window overlay retained;
terminal focus could not be reliably restored, not proof of guest deadlock.
No dropped-frame count or global performance claim.
