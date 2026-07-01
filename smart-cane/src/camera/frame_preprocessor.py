"""Frame preprocessing: ROI cropping and resize before inference — RF05."""
try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None


def crop_roi(frame, config):
    """Crop the frame to the configured region of interest (above-waist
    priority): ignores the extreme lower part of the image by default."""
    if frame is None:
        return None
    cam_cfg = config.section("camera")
    h, w = frame.shape[0], frame.shape[1]
    top = int(cam_cfg.get("roi_top", 0.0) * h)
    bottom = int(cam_cfg.get("roi_bottom", 1.0) * h)
    left = int(cam_cfg.get("roi_left", 0.0) * w)
    right = int(cam_cfg.get("roi_right", 1.0) * w)
    return frame[top:bottom, left:right]


def resize(frame, width, height):
    if frame is None:
        return None
    if cv2 is not None:
        return cv2.resize(frame, (width, height))
    return frame


def preprocess(frame, config):
    """Full RF05 pipeline: crop to ROI, then resize to the AI model's input size."""
    cam_cfg = config.section("camera")
    cropped = crop_roi(frame, config)
    return resize(cropped, cam_cfg.get("width", 320), cam_cfg.get("height", 320))


def horizontal_position(bbox_center_x, frame_width):
    """Map a bounding-box center x-coordinate to esquerda/centro/direita (RF03)."""
    ratio = bbox_center_x / frame_width if frame_width else 0.5
    if ratio < 0.4:
        return "esquerda"
    if ratio > 0.6:
        return "direita"
    return "centro"
