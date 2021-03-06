#!/usr/bin/env python
#
# Copyright (C) 2011, 2012  Strahinja Val Markovic  <val@markovic.io>
#
# This file is part of YouCompleteMe.
#
# YouCompleteMe is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# YouCompleteMe is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with YouCompleteMe.  If not, see <http://www.gnu.org/licenses/>.

import re
import vim
from ycm import vimsupport
from ycm import utils
from ycm import user_options_store
import ycm_client_support

YCM_VAR_PREFIX = 'ycm_'


def BuildServerConf():
  """Builds a dictionary mapping YCM Vim user options to values. Option names
  don't have the 'ycm_' prefix."""

  vim_globals = vimsupport.GetReadOnlyVimGlobals( force_python_objects = True )
  server_conf = {}
  for key, value in vim_globals.items():
    if not key.startswith( YCM_VAR_PREFIX ):
      continue
    try:
      new_value = int( value )
    except:
      new_value = value
    new_key = key[ len( YCM_VAR_PREFIX ): ]
    server_conf[ new_key ] = new_value

  return server_conf


def LoadJsonDefaultsIntoVim():
  defaults = user_options_store.DefaultOptions()
  vim_defaults = {}
  for key, value in defaults.iteritems():
    vim_defaults[ 'ycm_' + key ] = value

  vimsupport.LoadDictIntoVimGlobals( vim_defaults, overwrite = False )


def CompletionStartColumn():
  """Returns the 0-based index where the completion string should start. So if
  the user enters:
    foo.bar^
  with the cursor being at the location of the caret, then the starting column
  would be the index of the letter 'b'.
  """

  line = vim.current.line
  start_column = vimsupport.CurrentColumn()

  while start_column > 0 and utils.IsIdentifierChar( line[ start_column - 1 ] ):
    start_column -= 1
  return start_column


def CurrentIdentifierFinished():
  current_column = vimsupport.CurrentColumn()
  previous_char_index = current_column - 1
  if previous_char_index < 0:
    return True
  line = vim.current.line
  try:
    previous_char = line[ previous_char_index ]
  except IndexError:
    return False

  if utils.IsIdentifierChar( previous_char ):
    return False

  if ( not utils.IsIdentifierChar( previous_char ) and
       previous_char_index > 0 and
       utils.IsIdentifierChar( line[ previous_char_index - 1 ] ) ):
    return True
  else:
    return line[ : current_column ].isspace()


def LastEnteredCharIsIdentifierChar():
  current_column = vimsupport.CurrentColumn()
  previous_char_index = current_column - 1
  if previous_char_index < 0:
    return False
  line = vim.current.line
  try:
    previous_char = line[ previous_char_index ]
  except IndexError:
    return False

  return utils.IsIdentifierChar( previous_char )


def AdjustCandidateInsertionText( candidates ):
  """This function adjusts the candidate insertion text to take into account the
  text that's currently in front of the cursor.

  For instance ('|' represents the cursor):
    1. Buffer state: 'foo.|bar'
    2. A completion candidate of 'zoobar' is shown and the user selects it.
    3. Buffer state: 'foo.zoobar|bar' instead of 'foo.zoo|bar' which is what the
    user wanted.

  This function changes candidates to resolve that issue.

  It could be argued that the user actually wants the final buffer state to be
  'foo.zoobar|' (the cursor at the end), but that would be much more difficult
  to implement and is probably not worth doing.
  """

  def NewCandidateInsertionText( to_insert, word_after_cursor ):
    if to_insert.endswith( word_after_cursor ):
      return to_insert[ : - len( word_after_cursor ) ]
    return to_insert

  match = re.search( r'^(\w+)', vimsupport.TextAfterCursor() )
  if not match:
    return candidates

  new_candidates = []

  word_after_cursor = match.group( 1 )
  for candidate in candidates:
    if type( candidate ) is dict:
      new_candidate = candidate.copy()

      if not 'abbr' in new_candidate:
        new_candidate[ 'abbr' ] = new_candidate[ 'word' ]

      new_candidate[ 'word' ] = NewCandidateInsertionText(
        new_candidate[ 'word' ],
        word_after_cursor )

      new_candidates.append( new_candidate )

    elif type( candidate ) is str:
      new_candidates.append(
        { 'abbr': candidate,
          'word': NewCandidateInsertionText( candidate, word_after_cursor ) } )
  return new_candidates


COMPATIBLE_WITH_CORE_VERSION = 7

def CompatibleWithYcmCore():
  try:
    current_core_version = ycm_client_support.YcmCoreVersion()
  except AttributeError:
    return False

  return current_core_version == COMPATIBLE_WITH_CORE_VERSION


