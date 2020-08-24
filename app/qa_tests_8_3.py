import matplotlib.pyplot as plt
import numpy as np
import math
import os
import cv2
import pydicom
from pymongo import MongoClient
import pprint
import sys
import random
from collections import OrderedDict
from skimage import morphology
from pydicom.filereader import read_dicomdir

np.set_printoptions(threshold=sys.maxsize)


def load_scan(path, x=0, y=100):
    print("Loading scan...")
    slices = [pydicom.dcmread(path + '/' + s) for s in os.listdir(path)[x:y]]
    return slices


def get_pixels_hu(scans):
    # converts one DICOM scan to an np array in Hounsfield Units
    pixarray = []
    for s in scans:
        pixarray.extend(s.pixel_array)
    img = np.stack(pixarray)
    img = img.astype(np.float64)
    img[img == -2000] = 0

    # converts to Hounsfield units (HU)
    intercept = scans[0].RescaleIntercept if 'RescaleIntercept' in scans[0] else -1024
    slope = scans[0].RescaleSlope if 'RescaleSlope' in scans[0] else 1

    if slope != 1:
        img = slope * img.astype(np.float64).astype(np.int16)

    img += np.int16(intercept)
    return np.array(img, dtype=np.int16)


def get_pixels_stack(scans):
    # converts a stack of DICOM scans to an array of np arrays in Hounsfield Units
    pixarray = []
    for s in scans:
        pixarray.append(s.pixel_array)
    img = np.stack(pixarray)
    img = img.astype(np.float64)
    img[img == -2000] = 0
    # converts to Hounsfield units (HU)
    intercept = scans[0].RescaleIntercept if 'RescaleIntercept' in scans[0] else -1024
    slope = scans[0].RescaleSlope if 'RescaleSlope' in scans[0] else 1

    if slope != 1:
        img = slope * img.astype(np.float64).astype(np.int16)

    img += np.int16(intercept)
    return np.array(img, dtype=np.int16)


def display_hounsfield(stack):
    # displays a histogram of the distribution of hounsfield units in the stack of scans
    # input: (np) array
    print("Displaying Hounsfield...")
    (n, bins, patches) = plt.hist(stack.flatten(), bins=50, color='c')
    plt.xlabel("Hounsfield Units (HU)")
    plt.ylabel("Frequency")
    # plt.ylim(0, 2000)
    print(n, bins)

    plt.show()


def sample_stack(stack, rows=6, cols=6, start_with=0, show_every=2):
    # displays scans in the stack
    print("Sample stack")
    fig, ax = plt.subplots(rows, cols, figsize=[12, 12])
    for i in range(rows * cols):
        ind = start_with + i * show_every
        ax[int(i / rows), int(i % rows)].set_title('Slice %d' % ind)
        ax[int(i / rows), int(i % rows)].imshow(stack[ind], cmap='gray')
        ax[int(i / rows), int(i % rows)].axis('off')

    plt.show()


def mask_seg(dicom_img, min_threshold, max_threshold):
    # masks scan for Module 1 based on a minimum and maximum threshold
    img = get_pixels_hu([dicom_img])
    pixel_space = dicom_img.PixelSpacing[0]
    hu_area = int(100 / pixel_space ** 2)

    # removing irrelevant areas
    mask = cv2.inRange(img, min_threshold, max_threshold).astype(bool)
    mask = morphology.remove_small_objects(mask, hu_area, connectivity=1).astype(int)
    img *= mask
    mask = mask.astype(bool)
    mask = morphology.remove_small_objects(mask, 50000, connectivity=1)
    mask = np.invert(mask).astype(int)
    img *= mask

    # crops image to relevant area (where values are not 0)
    true_points = np.argwhere(img)
    top_left = true_points.min(axis=0, initial=None)
    bottom_right = true_points.max(axis=0, initial=None)

    module = img[top_left[0]:bottom_right[0] + 1,  # plus 1 because slice isn't
                 top_left[1]:bottom_right[1] + 1]  # inclusive
    center_of_mass = ((top_left[1]+bottom_right[1]+1)//2, (top_left[0]+bottom_right[0]+1)//2)
    return module, center_of_mass


def separate_series(dicom_imgs):
    # TODO: update this
    series = OrderedDict([])
    for img in dicom_imgs:
        description = img.SeriesDescription.split()[0]
        try:
            series[description].append(img)
        except:
            if len(series) < 5:
                series[description] = [img]
    return series


def define_circle(img, coords, pixel_space, circ_area=100, display=False):
    # crops a circle in the given image using the center coordinates and required area (in mm)
    radius = int(math.sqrt(circ_area / np.pi) / pixel_space)
    mask = np.zeros(img.shape, dtype=np.uint8)
    cv2.circle(mask, coords, radius, (1, 1, 1), thickness=-1, lineType=8, shift=0)
    result = mask * img
    extracted_result = result[coords[1] - radius:coords[1] + radius,
                              coords[0] - radius:coords[0] + radius]
    if display:
        plt.imshow(extracted_result)
        plt.show()
    return extracted_result


def calculate_roi(img):
    img_mean = round(float(np.nanmean(np.where(np.isclose(img, 0), np.nan, img))), 2)
    std = round(float(np.nanstd(np.where(np.isclose(img, 0), np.nan, img))), 2)
    return {'Mean': img_mean, 'Standard Deviation': std}


def get_uniformity_coords(img, dicom_img):
    # given a cropped image of the phantom, locate coordinates of each ROI
    # 12', 3', 6', 9', and the center
    pixel_space = dicom_img.PixelSpacing[0]
    radius = int(math.sqrt(400 / np.pi) / pixel_space)
    shape = img.shape
    coord_set = {"12'": (shape[0] // 2, radius * 2),
                 "6'": (shape[0] // 2, shape[1] - radius * 2),
                 "9'": (radius * 2, shape[1] // 2),
                 "3'": (shape[0] - radius * 2, shape[1] // 2),
                 "Center": (shape[0] // 2, shape[1] // 2)}
    return coord_set


def hu_reproducibility(dicom_img, color=(255, 255, 0), thickness=2):
    # given an image
    image = get_pixels_hu([dicom_img])
    thresholds = {"Polyethylene": (-200, -50),
                  "Acrylic": (50, 500),
                  "Bone": (500, 2000),
                  "Air": (-2000, -500)
                  }
    results = {}
    coordinates = {}
    for threshold in thresholds:
        img, coords = mask_seg(dicom_img, thresholds[threshold][0], thresholds[threshold][1])
        coordinates[threshold] = coords
        circ = define_circle(img, (img.shape[0] // 2, img.shape[1] // 2), float(dicom_img.PixelSpacing[0]))
        results[threshold] = calculate_roi(circ)
    for coord in coordinates:
        image = cv2.circle(image, coordinates[coord], radius=14, color=color, thickness=thickness)
    coordinates = list(coordinates.values())
    water_y = int(sum(n for _, n in coordinates)/len(coordinates))
    x = np.mean(int(sum(n for n, _ in coordinates)/len(coordinates)))
    diff = np.abs(x - max(coordinates, key=lambda i: i[0])[0]) * .4
    water_x = int(min(coordinates, key=lambda i: i[0])[0] - diff)
    water_coords = (water_x, water_y)
    circ = define_circle(image, water_coords, float(dicom_img.PixelSpacing[0]))
    image = cv2.circle(image, water_coords, radius=14, color=color, thickness=thickness)
    results["Water"] = calculate_roi(circ)
    return results, image


def low_contrast_resolution(dicom_img, color=(255, 255, 0), thickness=2):
    # Performs test on the contrast between the 25mm disk and center region of the slice
    img = get_pixels_hu([dicom_img])
    mask = cv2.inRange(img, 50, 1000).astype(bool).astype(int)
    img *= mask
    true_points = np.argwhere(img)
    top_left = true_points.min(axis=0, initial=None)
    bottom_right = true_points.max(axis=0, initial=None)
    module = img[top_left[0]:bottom_right[0] + 1,
                 top_left[1]:bottom_right[1] + 1]
    disk_coordinates = (module.shape[0] // 2, int(module.shape[1] * .18))
    background_coordinates = (int(module.shape[0]*.36), int(module.shape[1]*.2))
    circ_area = 100
    pixel_space = dicom_img.PixelSpacing[0]
    disk_circ = define_circle(module, disk_coordinates, pixel_space, circ_area=circ_area)
    bkgd_circ = define_circle(module, background_coordinates, pixel_space, circ_area=circ_area)
    disk = calculate_roi(disk_circ)
    bkgd = calculate_roi(bkgd_circ)
    mean_disk = disk["Mean"]
    mean_bkgd = bkgd["Mean"]
    std_bkgd = bkgd["Standard Deviation"]
    contrast_to_noise_ratio = round(np.abs(mean_disk - mean_bkgd) / std_bkgd, 2)
    results = {
        "Mean Disk (HU)": mean_disk,
        "Mean Background (HU)": mean_bkgd,
        "Standard Deviation Background (HU)": std_bkgd,
        "Contrast to Noise Ratio": contrast_to_noise_ratio
    }

    # Drawing ROI on original image
    radius = int(math.sqrt(circ_area / np.pi) / pixel_space)
    module = cv2.circle(module, disk_coordinates, radius, color, thickness)
    module = cv2.circle(module, background_coordinates, radius, color, thickness)

    return results, module


def uniformity_assessment(dicom_img, color=(255, 255, 0), thickness=2):
    img = get_pixels_hu([dicom_img])
    mask = cv2.inRange(img, -100, 1000).astype(bool).astype(int)
    img *= mask
    true_points = np.argwhere(img)
    top_left = true_points.min(axis=0, initial=None)
    bottom_right = true_points.max(axis=0, initial=None)
    module = img[top_left[0]:bottom_right[0] + 1,
                 top_left[1]:bottom_right[1] + 1]
    coords = get_uniformity_coords(module, dicom_img)
    results = {}
    imgs_total = np.array([])
    circ_area = 400
    pixel_space = float(dicom_img.PixelSpacing[0])
    radius = int(math.sqrt(circ_area / np.pi) / pixel_space)
    for coord in coords:
        circ = define_circle(module, coords[coord], pixel_space, circ_area=circ_area)
        results[coord] = calculate_roi(circ)
        imgs_total = np.concatenate((imgs_total, np.ndarray.flatten(circ)))
        module = cv2.circle(module, coords[coord], radius, color, thickness)
    results["Mean"] = round(((results["12'"]["Mean"] +
                              results["6'"]["Mean"] +
                              results["9'"]["Mean"] +
                              results["3'"]["Mean"] +
                              results["Center"]["Mean"]) / 5), 2)
    results["Standard Deviation"] = round(float(np.nanstd(np.where(np.isclose(imgs_total, 0), np.nan, imgs_total))), 2)
    return results, module


def get_study_information(dicom):
    # protocols = {}
    # try:
    #     protocols['Survey Date'] = dicom.StudyDate
    # except AttributeError:
    #     protocols['Survey Date'] = 'N/A'
    # try:
    #
    protocols = {'Survey Date': dicom.StudyDate,
                 'Protocol Name': dicom.ProtocolName,
                 'kVp': float(dicom.KVP),
                 'Time per rotation (s)': float(dicom.ExposureTime) / 1000,
                 'mA': int(dicom.XRayTubeCurrent),
                 'Real mAs': int(dicom.XRayTubeCurrent) * float(dicom.ExposureTime) / 1000,
                 'SFOV (cm)': int(dicom.DataCollectionDiameter) / 10,
                 'Reconstruction Algorithm': dicom.ConvolutionKernel,
                 'Axial or Helical': dicom.ImageType[2],
                 'Image Thickness': dicom.SliceThickness}
    return protocols


def run_tests(dicom_imgs):
    # creates JSON format data, with image attributes and quality assurance test results
    # Input: set of dicom images split by study description
    name = random.choice(list(dicom_imgs))
    quality_control = OrderedDict({"_id": int(dicom_imgs[name][0].StudyDate),
                                   "Protocols": get_study_information(dicom_imgs[name][0]),
                                   "HU Reproducibility": {},
                                   "Low Contrast Resolution": {}})
    image_results = []
    # Module 1
    for img_set in dicom_imgs:
        quality_control['HU Reproducibility'][img_set], image = hu_reproducibility(dicom_imgs[img_set][0])
        image_results.append(image)
    # Module 2
    for img_set in dicom_imgs:
        if max(dicom_slice.SliceLocation for dicom_slice in dicom_imgs[img_set]) > 35:
            working_img = dicom_imgs[img_set][0]
            for image in dicom_imgs[img_set]:
                if np.abs(float(working_img.SliceLocation) - 40) > np.abs(float(image.SliceLocation) - 40):
                    working_img = image
            quality_control['Low Contrast Resolution'][img_set], image = low_contrast_resolution(working_img)
            image_results.append(image)
    # Module 3
    first = list(dicom_imgs)[0]
    quality_control['Uniformity Assessment'], image = uniformity_assessment(dicom_imgs[first][9])
    image_results.append(image)

    for x in image_results:
        plt.imshow(x)
        plt.show()
    return quality_control


def push_seq_to_database(data_set, db_name):
    # enters the data_set into Project Charon MongoDB under the given db_name
    print("Pushing to database...")
    client = MongoClient(
        "mongodb+srv://jollypolly123:Micron66Dodged*@cluster0.lakbb.mongodb.net/Cluster0?retryWrites=true&w=majority")
    db = client.quality_control

    result = getattr(db, db_name).insert_one(data_set)
    print("Finished as {}".format(result.inserted_id))


def update_database(info):
    print("Updating database...")
    # TODO: change this


if __name__ == "__main__":
    imgs = load_scan("C:\\Users\\jolly\\Programming\\PythonProjects\\Z&A\\set4\\DMI HOLLYWOOD")
    series_set = separate_series(imgs)
    test_results = run_tests(series_set)
    push_seq_to_database(test_results, "Three Modules")

# Window/webapp
# Django; select directory; load dicomdir or folder

# Graphs

# Display img with ROI for modules

# Module 4: Review spatial resolution evaluation in MATLAB for CATPhan (MTF); then display ROI
