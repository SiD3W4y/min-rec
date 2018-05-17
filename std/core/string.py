def strlen(data):
    i = 0

    while data[i] != '\x00':
        i += 1

    return i
