#!/usr/bin/python
# -*- coding:utf-8 -*-
from flask import Blueprint

views_blueprint = Blueprint('views', __name__)

from . import Hello
from . import HR
# from . import ConvenienceStore
from . import Flnet
from . import fulearnV1
from . import fulearnV4
from . import fulearnV4_User
from . import fulearnV4_Class
from . import fulearnV4_Group
from . import fulearnV4_UseKind
from . import fulearnV4_Post
from . import fulearnOldAPI
from . import iStudyV1
from . import fulearnV4_Operation
from . import fulearnV4_Department
from . import Collect_Post
from . import demoapi
from . import wirelist
from . import fixture