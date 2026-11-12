"""Display-PNG boards for measured real-mask comparisons; preserves native crop pixels."""
import json


def boards(out):
    """Make full, enlarged-close and native 1:1 per-surface boards from display PNGs."""
    from PIL import Image, ImageDraw, ImageChops, ImageEnhance
    from edge_lab_common import board_views
    results = json.loads((out / 'measurements.json').read_text())
    for kind, layer in results['layers'].items():
        folder = out / kind
        keys = ['off', 'procedural'] + [row['candidate']['id'] for row in layer['candidates']]
        labels = {'off': 'off', 'procedural': 'procedural'}
        for index, row in enumerate(layer['candidates']):
            candidate = row['candidate']
            labels[candidate['id']] = 'mask-' + chr(97 + index) + ' | ' + candidate['id'] + ' | ' + candidate['scan']
        images = {key: Image.open(folder / (key + '.png')).convert('RGB') for key in keys}
        for key in keys[1:]:
            diff = ImageChops.difference(images[key], images['off'])
            ImageEnhance.Brightness(diff).enhance(6).save(folder / (key + '-off-diff-x6.png'))
        for image in images.values():
            painter = ImageDraw.Draw(image)
            for name, rectangle in layer['regions'].items():
                painter.text((rectangle[0], 25), name, fill='black')
        labelled = {labels[key]: image for key, image in images.items()}
        labelled['all-on'] = images['procedural']
        (folder / 'regions.json').write_text(json.dumps({'crop': [360, 65, 650, 355]}))
        # Use the shared full board; the all-material native board below owns the close view.
        next(board_views(folder, labelled, len(keys), [labels[key] for key in keys], 8))
        # Each row is a material; each column is a source. Native crops are never resampled.
        width = max(rect[2] - rect[0] for rect in layer['regions'].values())
        height = max(rect[3] - rect[1] for rect in layer['regions'].values())
        native = Image.new('RGB', (width * len(keys), (height + 52) * len(layer['regions'])), '#202020')
        draw = ImageDraw.Draw(native)
        for row_index, (name, rectangle) in enumerate(layer['regions'].items()):
            for column, key in enumerate(keys):
                x, y = column * width, row_index * (height + 52)
                native.paste(images[key].crop(tuple(rectangle)), (x, y + 52))
                draw.text((x + 4, y + 4), name + ' | ' + labels[key], fill='white')
                stats = layer['procedural'][name] if key == 'procedural' else next(
                    (candidate['tiles'][name] for candidate in layer['candidates'] if candidate['candidate']['id'] == key), None)
                label = 'off: factor=0' if stats is None else 'mean %.4f sd %.4f cov %.3f' % tuple(stats[k] for k in ('mean', 'sd', 'coverage'))
                draw.text((x + 4, y + 23), label, fill='white')
        native.save(folder / 'board-native.png')
        native.resize((native.width * 2, native.height * 2), Image.Resampling.NEAREST).save(folder / 'board-close.png')
