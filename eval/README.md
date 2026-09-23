# Detector calibration test set

`scripts/calibrate_perception.py` needs a small held-out set that was **not** used for
training or validation, so the numbers it reports are honest.

Layout:
```
eval/
  images/*.jpg              # video frames, ideally from your own indoor camera footage
  labels.csv                # frame, class, present (1/0)  — ground truth per frame
```

`labels.csv` example:
```
frame,cls,present
images/f0001.jpg,fire,0
images/f0001.jpg,smoke,0
images/f0002.jpg,fire,1
images/f0002.jpg,smoke,1
```

About 300-500 frames, covering: clear corridors, real fire/smoke (or licensed footage —
never ignite anything yourself), and hard negatives (steam, warm lighting, red clothing,
fog) to measure the false-positive rate honestly. Split by source video, not by random
frame, so near-duplicate frames don't leak between "used to pick a threshold" and "used
to report a number" (this script doesn't pick a threshold — it evaluates the one you pass).
