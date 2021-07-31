from wand.image import Image


def incinerate(*images):
    for image in images:
        image: Image
        image.destroy()