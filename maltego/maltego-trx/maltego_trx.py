"""Transforms for file listing in a directory.

Improvements:
- use `os.scandir` for efficiency
- better error handling and informative UI messages
- set the entity value to the full file path
"""

import os
from maltego_trx.transform import DiscoverableTransform


class ListFiles(DiscoverableTransform):
    """Returns files contained within a directory as `maltego.File` entities."""

    @classmethod
    def create_entities(cls, request, response):
        folder_path = request.Value

        if not os.path.exists(folder_path):
            response.addUIMessage(f"Path not found: {folder_path}", messageType='PartialError')
            return

        if not os.path.isdir(folder_path):
            response.addUIMessage("Input is not a directory.", messageType='PartialError')
            return

        # determine recursion settings: environment overrides and optional request params
        def _get_req_param(name: str):
            # try several common request APIs/members gracefully
            try:
                if hasattr(request, 'getProperty'):
                    v = request.getProperty(name)
                    if v is not None:
                        return v
            except Exception:
                pass
            try:
                if hasattr(request, 'getPropertyValue'):
                    v = request.getPropertyValue(name)
                    if v is not None:
                        return v
            except Exception:
                pass
            # fallback to attribute dicts if available
            for attr in ('Properties', 'Fields', 'params'):
                val = getattr(request, attr, None)
                if isinstance(val, dict) and name in val:
                    return val.get(name)
            return None

        # recursion now enabled by default; set LISTFILES_RECURSIVE=0 to disable
        env_recursive = os.environ.get('LISTFILES_RECURSIVE', '1').lower() in ('1', 'true', 'yes')
        env_maxdepth = os.environ.get('LISTFILES_MAXDEPTH')

        req_recursive = _get_req_param('recursive')
        req_maxdepth = _get_req_param('max_depth') or _get_req_param('maxdepth')

        recursive = env_recursive
        if req_recursive is not None:
            recursive = str(req_recursive).lower() in ('1', 'true', 'yes')

        max_depth = None
        if req_maxdepth is not None:
            try:
                max_depth = int(req_maxdepth)
            except Exception:
                max_depth = None
        elif env_maxdepth is not None:
            try:
                max_depth = int(env_maxdepth)
            except Exception:
                max_depth = None

        def iter_files(path: str, cur_depth: int = 0):
            # yield (file path, depth); if max_depth is None => unlimited depth; if 0 => current dir only
            try:
                with os.scandir(path) as it:
                    for entry in it:
                        try:
                            if entry.is_file(follow_symlinks=False):
                                yield (entry.path, cur_depth)
                            elif recursive and entry.is_dir(follow_symlinks=False):
                                if max_depth is None or cur_depth < max_depth:
                                    yield from iter_files(entry.path, cur_depth + 1)
                        except PermissionError:
                            response.addUIMessage(f"Permission denied for {getattr(entry, 'path', str(entry))}", messageType='PartialError')
                        except OSError as e:
                            response.addUIMessage(f"Error processing {getattr(entry, 'path', str(entry))}: {e}", messageType='PartialError')
            except PermissionError:
                response.addUIMessage(f"Permission Denied: {path}", messageType='PartialError')
            except OSError as e:
                response.addUIMessage(f"Error listing directory {path}: {e}", messageType='PartialError')

        total = 0
        for fp, depth in iter_files(folder_path, 0):
            try:
                ent = response.addEntity("maltego.File", fp)
                ent.addProperty("path", "Path", "strict", fp)
                # store depth as an integer value to preserve numeric semantics
                # depth as strict integer property
                ent.addProperty("depth", "Depth", "strict", depth)
                # parent directory
                parent = os.path.dirname(fp)
                ent.addProperty("parent", "Parent", "strict", parent)
                # relative path from the requested folder
                try:
                    rel = os.path.relpath(fp, folder_path)
                except Exception:
                    rel = fp
                ent.addProperty("relative_path", "Relative Path", "strict", rel)
                try:
                    size = os.path.getsize(fp)
                    ent.addProperty("filesize", "File Size", "loose", str(size))
                except OSError as e:
                    response.addUIMessage(f"Could not read size for {fp}: {e}", messageType='PartialError')
                total += 1
            except Exception as e:
                response.addUIMessage(f"Failed to add entity for {fp}: {e}", messageType='PartialError')

        msg = f"Added {total} file(s) from {folder_path}"
        if recursive:
            msg += " (recursive)"
            if max_depth is not None:
                msg += f", max_depth={max_depth}"
        response.addUIMessage(msg)