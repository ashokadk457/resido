def getSum(n):
    sum = 0
    for digit in str(n):
        sum += int(digit)
    return sum


def check_npi(npi):
    if npi.startswith("009900"):
        # TODO Sample NPI
        return True
    if not npi.isdecimal():
        return False
    if len(npi) != 10:
        return False
    last = int(npi[9])
    nums = []
    sum = 0
    for i in range(0, len(npi) - 1):
        if i % 2 == 0:
            sum += getSum(2 * int(npi[i]))
            nums.append(2 * int(npi[i]))
        else:
            sum += int(npi[i])
            nums.append(int(npi[i]))
    total = sum + 24
    units = total % 10
    checkDigit = (10 - units) if (units != 0) else units
    if last == checkDigit:
        return True
    else:
        return False
