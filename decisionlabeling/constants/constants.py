class FrameRate:
    VIEW_FRAME_RATE = 70
    TAG_FRAME_RATE = 45

class FrameMode:
    MANUAL = "manual"  # for manually choosing the current frame
    CONTROLLED = "controlled"  # when the current frame is being controlled by some thread (Player, Tracker, ...)
    SLIDER = "slider"


class RightClickOption:
    DELETE_CURRENT = 0
    DELETE_PREVIOUS = 1
    DELETE_FOLLOWING = 2

