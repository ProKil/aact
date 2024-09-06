# import cv2
from .base import DataModel
from .commons import DataEntry

from pydantic import ValidationError

from logging import getLogger


def read_data_from_jsonl(
    jsonl_file_path: str, data_model: type[DataModel], arrange_by_channel: bool = False
) -> list[DataEntry[DataModel]] | dict[str, list[DataEntry[DataModel]]]:
    logger = getLogger(__name__)

    data_entries: list[DataEntry[DataModel]] = []
    data_by_channel: dict[str, list[DataEntry[DataModel]]] = {}

    with open(jsonl_file_path, "r") as f:
        for lineno, line in enumerate(f.readlines()):
            try:
                data_entry = DataEntry[data_model].model_validate_json(line)  # type: ignore[valid-type]
            except ValidationError as e:
                logger.error(
                    f"Validation error at Line {lineno}: {e}. Skipping this line."
                )
                continue
            if arrange_by_channel:
                if data_entry.channel not in data_by_channel:
                    data_by_channel[data_entry.channel] = []
                data_by_channel[data_entry.channel].append(data_entry)
            else:
                data_entries.append(data_entry)

    if arrange_by_channel:
        return data_by_channel
    else:
        return data_entries


# def get_frame_size(frame_bytes: bytes) -> tuple[int, int]:
#     """
#     Get the dimensions (width, height) of a frame in bytes.

#     Args:
#     - frame_bytes: A single frame in bytes.

#     Returns:
#     - (width, height): A tuple representing the frame's dimensions.
#     """
#     # Convert bytes to a numpy array
#     np_frame = np.frombuffer(frame_bytes, dtype=np.uint8)

#     # Decode the numpy array to get the frame
#     frame = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)

#     # Get the dimensions of the frame
#     height, width, _ = frame.shape

#     return (width, height)


# def frames_to_mp4(
#     frame_data_entries: list[DataEntry[Image]], output_mp4_path: str
# ) -> None:
#     """
#     Convert a list of frames in bytes to a video file.

#     Args:
#     - frames: List of frames, where each frame is in bytes.
#     - output_path: Path to save the output video.
#     - fps: Frames per second for the output video.
#     - frame_size: Tuple representing the size of the frames (width, height).

#     Returns:
#     - None
#     """

#     logger = getLogger(__name__)
#     assert len(frame_data_entries) > 0, "Frame data entries list is empty"
#     time_span = (
#         frame_data_entries[-1].timestamp - frame_data_entries[0].timestamp
#     ).total_seconds()
#     fps = len(frame_data_entries) / time_span

#     frames = [frame.data.image for frame in frame_data_entries]
#     frame_size = get_frame_size(frames[0])

#     logger.info(
#         f"Converting {len(frames)} frames to video at {fps} FPS. Frame size: {frame_size}"
#     )

#     # Initialize the video writer
#     fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore[attr-defined]
#     out = cv2.VideoWriter(output_mp4_path, fourcc, fps, frame_size)

#     for frame_bytes in frames:
#         # Convert bytes to a numpy array
#         np_frame = np.frombuffer(frame_bytes, dtype=np.uint8)

#         # Decode the numpy array to get the frame
#         frame = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)

#         # Write the frame to the video file
#         out.write(frame)

#     # Release the video writer
#     out.release()
