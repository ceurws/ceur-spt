"""
Created on 2022-09-11

@author: wf
"""
import ceurspt


class Version(object):
    """
    Version handling for VolumeBrowser
    """
    name = ""
    version = ceurspt.__version__
    date = '2023-03-17'
    updated = '2023-03-17'
    description = 'CEUR-WS Single Point of Truth RestFUL server',

    authors = 'Tim Holzheim, Wolfgang Fahl'

    doc_url = "https://github.com/ceurws/ceur-spt"
    chat_url = "https://github.com/ceurws/ceur-spt/discussions"
    cm_url = "https://github.com/ceurws/ceur-spt"

    license = f'''Copyright 2023 contributors. All rights reserved.

  Licensed under the Apache License 2.0
  https://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.'''
    longDescription = f"""{name} version {version}
{description}

  Created by {authors} on {date} last updated {updated}"""
