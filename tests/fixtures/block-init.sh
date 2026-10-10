#!/bin/busybox sh
export PATH=/bin

fail() {
    printf '{"event":"loti.vm.error","reason":"%s"}\n' "$1"
    cat /tmp/error 2>/dev/null
    poweroff -f
    exit 1
}

/bin/vm-mount 2>/tmp/error || fail guest_mount
printf '{"event":"loti.vm.kernel","release":"%s"}\n' "$(uname -r)"
for specification in 'vda:0' 'vdb:512' 'vdc:33280' 'vdd:131584'; do
    device=${specification%:*}
    size=${specification#*:}
    attempts=0
    while [ ! -b "/dev/$device" ]; do
        attempts=$((attempts + 1))
        [ "$attempts" -lt 100 ] || fail missing_device
        sleep 0.01
    done
    for program in readv raw-cat cat cp; do
        actual=/tmp/$program-$size
        exit_code=0
        if [ "$program" = cp ]; then
            /examples/cp "/dev/$device" "$actual" 2>/tmp/error || exit_code=$?
        else
            /examples/$program "/dev/$device" >"$actual" 2>/tmp/error || exit_code=$?
        fi
        result=pass
        if [ "$program" = cp ] && [ -e /expect-copy-rejection ]; then
            [ "$exit_code" = 1 ] || fail copy_rejection_exit
            [ "$(head -n 1 /tmp/error)" = 'error: ExpectedRegularInputFile' ] || fail copy_rejection_class
            result=known_bug
        else
            [ "$exit_code" = 0 ] || fail example_exit
            cmp "/fixtures/$size.raw" "$actual" || fail byte_mismatch
        fi
        printf '{"event":"loti.vm.case","program":"%s","size":%s,"exit_code":%s,"result":"%s"}\n' "$program" "$size" "$exit_code" "$result"
    done
done
printf '{"event":"loti.vm.complete","cases":16}\n'
poweroff -f
