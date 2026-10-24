"""Build relocatable ARM payloads from the pinned CodeWarrior ELF output.

Internal PC-relative branches need no relocation. The final ELF retains internal
ABS32 fixups, while object relocation records recover literals referring to
absolute linker symbols and identify external PC24 calls that must be adjusted
when a heap-loaded payload moves. No instruction scanning.
"""
import io
import struct
from elftools.elf.elffile import ELFFile


def relocations(obj_path, elf_path, base, payload):
    final = ELFFile(io.BytesIO(elf_path.read_bytes()))
    symtab = final.get_section_by_name('.symtab')
    values = {s.name: s['st_value'] for s in symtab.iter_symbols()}
    records = set()
    for section in final.iter_sections():
        if section['sh_type'] not in ('SHT_REL', 'SHT_RELA'):
            continue
        for relocation in section.iter_relocations():
            if relocation['r_info_type'] == 1:
                target = final.get_section(section['sh_link']).get_symbol(relocation['r_info_sym'])
                if base <= target['st_value'] < base + len(payload):
                    continue
                raise ValueError('Unexpected external linked PC24 relocation')
            if relocation['r_info_type'] != 2:
                raise ValueError('Unsupported linked relocation')
            offset = relocation['r_offset'] - base
            if not 0 <= offset <= len(payload) - 4:
                raise ValueError('Relocation outside payload')
            value = struct.unpack_from('<I', payload, offset)[0]
            if not base <= value < base + len(payload):
                raise ValueError('Expected an internal absolute address')
            records.add(offset)
    obj = ELFFile(io.BytesIO(obj_path.read_bytes()))
    symbols = obj.get_section_by_name('.symtab')
    functions = {}
    for s in symbols.iter_symbols():
        if s['st_info']['type'] == 'STT_FUNC' and isinstance(s['st_shndx'], int):
            functions.setdefault(s['st_shndx'], []).append(s)
    for section in obj.iter_sections():
        if section['sh_type'] not in ('SHT_REL', 'SHT_RELA'):
            continue
        for relocation in section.iter_relocations():
            kind = relocation['r_info_type']
            if kind not in (1, 2):
                continue
            target = symbols.get_symbol(relocation['r_info_sym'])
            if target['st_shndx'] != 'SHN_UNDEF':
                continue
            internal = base <= values.get(target.name, 0) < base + len(payload)
            if (kind == 1 and internal) or (kind == 2 and not internal):
                continue
            offset = relocation['r_offset']
            owner = next((s for s in functions.get(section['sh_info'], [])
                          if s['st_value'] <= offset < s['st_value'] + s['st_size']), None)
            if owner is None:
                raise ValueError('External branch has no owning function')
            linked = values[owner.name] + offset - owner['st_value'] - base
            if not 0 <= linked <= len(payload) - 4:
                raise ValueError('Branch outside payload')
            word = struct.unpack_from('<I', payload, linked)[0]
            if kind == 2:
                # Absolute linker definitions lose their final ELF relocation.
                # In particular, a CodeWarrior tail-call veneer contains an
                # LDR/BX address literal pointing at an appended trampoline.
                # Recover its ABS32 record from the object, without scanning
                # instructions or mistaking ordinary constants for pointers.
                if not base <= word < base + len(payload):
                    raise ValueError('Internal ABS32 target outside payload')
                records.add(linked)
                continue
            if word & 0x0e000000 != 0x0a000000:
                raise ValueError('PC24 relocation is not an ARM branch')
            records.add(0x80000000 | linked)
    return sorted(records)


def pack(base, payload, entry, records):
    # Header + body + relocation words. Code/BSS stay word aligned.
    return (struct.pack('<6I', 0x31584248, base, len(payload), entry-base, len(records), 0)
            + payload + struct.pack('<' + 'I'*len(records), *records))
