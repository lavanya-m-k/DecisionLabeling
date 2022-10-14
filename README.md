# decisionlabeling

## Installation

Start by cloning the repository on your computer:
```bash
git clone https://github.com/lavanya-m-k/DecisionLabeling.git
cd DecisionLabeling
```

We recommend installing the required packages in a virtual environment to avoid any library versions conflicts. The following will do this for you:
```bash
virtualenv --no-site-packages venv
source venv/bin/activate
pip install -r requirements.txt
```

Otherwise, just install the requirements on your main Python environment using `pip` as follows:
```bash
pip install -r requirements
```

Finally, open the GUI using: 
```bash
python -m decisionlabeling.main
```


The data images and videos should be placed in the folder `data`, similarly to the client code.

To extract video files, use the following script:

```bash
bash extract.sh data/video_file.mp4
```

[//]: # ()
[//]: # (## Input / output)

[//]: # ()
[//]: # (To start labeling your videos, put these &#40;folder of images or video file, the frames will be extracted automatically&#41; inside the `data` folder. )

[//]: # ()
[//]: # (- Import labels: To import existing .CSV labels, hit `Cmd+I` &#40;or `Ctrl+I`&#41;. UltimateLabeling expects to read one .CSV file per frame, in the format: "class_id", "xc", "yc", "w", "h".)

[//]: # ()
[//]: # (- Export labels: The annotations are internally saved in the `output` folder. To export them in a unique .CSV file, hit `Cmd+E` &#40;or `Ctrl+E`&#41; and choose the destination location.)

[//]: # ()
[//]: # (If you need other file formats for your projects, please write a GitHub issue or submit a Pull request.)

[//]: # ()
[//]: # ()
[//]: # (## Shortcuts / mouse controls)

[//]: # ()
[//]: # (<img src="docs/keyboard_shortcuts.jpg" width="50%" />)

[//]: # ()
[//]: # (Keyboard:)

[//]: # (- A &#40;or Left key&#41;: next frame)

[//]: # (- D &#40;or Right key&#41;: previous frame)

[//]: # (- W/S: class up/down)

[//]: # (- T: start/stop tracking &#40;last used tracker&#41;)

[//]: # (- Numberpad: assign given class_id)

[//]: # (- Spacebar: play the video)



Mouse:

[//]: # (- Click: select bounding box)

[//]: # (- Click & hold: move in the image)

[//]: # (- Cmd + click & hold: create new bounding box)

[//]: # (- Right click: delete bounding box in current frame &#40;+ in all previous / all following frames if the corresponding option is enabled&#41;)
- Scroll wheel (or swipe up/down): zoom in the image 


## Improvements / issues
Please write a GitHub issue if you experience any issue or wish an improvement. Or even better, submit a pull request! 
