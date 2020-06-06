#!/usr/bin/python3

# Load enviroment vars
import os
from os.path import join, dirname
from dotenv import  load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)