---
title: BCI Drawing Tree Tool README
author: Tyler Lott
date: 7/14/2021
---

# BCI Drawing Tree Tool


* [Project Structure](#project-structure)
* [Compiling](#compiling)
* [BCI File Structure](#bci-file-structure)

# Project Structure
High level structure
* bin - contains application dependencies
* data - contains data for application as well as test cases
* docs - contains documentation for each class
* src - contains all of the main code files
  * gui
  * extractor
  * data_manager
  * runner.py - this is the main file of the program, run this, run the application
* tests - contains tests to ensure the program is functioning correctly, uses pytest 
* LICENSE - idk, I just slapped in the MIT open license
* README - this
* .pylintrc - the linting specs used on this project
* requirements.txt - all of the requirements for python env (python 3.7.4 btw)

# Compiling
To compile I used pyinstaller, the .spec file is in this directory and has all of the required inclusions. It is important that in the 'bin' folder tesseract, poppler, and upx are all included. The first two affect the function of the application. Tesseract for OCR and poppler for pdf to img. The other, upx, is a compressor for compiling to exe, it makes the final project MUCH smaller, which is important for distributing to the team, as the shared drive is usually slow af. 

# BCI File Structure

This file is literally just an hdf5 file. I named them bci files for some goof and gigs... I am tired.

Anyways, here is the file structure that the file uses. It's pretty simple and shoud be good unless a project has literally thousands of images for the pdfs

root
* ids : group
  * drawing 1
  * drawing 2
  * . . .
* images : group
  * drawing 1 : group -- attr{drawing_num, image_ids, parent}
    * page 1 : dataset
    * page 2 : dataset
    * . . .
* extracted_data : group
  * drawing 1 : group -- attr{drawing_num}
    * box 1 : group -- attr{image_id}
      * extracted_info 1 : dataset -- attr{drawing_num, boundingbox, image_id}
      * extracted_info 2
      * . . .
    * box 2
    * . . .
  * drawing 2
  * . . .



        