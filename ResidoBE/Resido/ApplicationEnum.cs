namespace Resido
{
    /// <summary>
    /// Defines the lock setting types.
    /// </summary>
    public enum LockSettingType
    {
        PrivacyLock = 2,
        TamperAlert = 3,
        ResetButton = 4,
        LockSound = 6,
        OpenDirection = 7,
        SoundVolume = 8,
        WifiPowerSaving = 10,
        DoorUnclosedAlarmTime = 11
    }

    public enum AccessRecordType
    {
        Face = -5,
        QrCode = -4,
        KeyboardPassword = 4,
        IcCard = 7,
        Fingerprint = 8,
        Remote = 55
    }

    /// <summary>
    /// Defines the method of adding a custom passcode.
    /// </summary>
    public enum OperationType
    {
        /// <summary>
        /// Add via phone Bluetooth.
        /// Requires calling APP SDK method to add passcode first, then sync to cloud.
        /// </summary>
        Bluetooth = 1,

        /// <summary>
        /// Add via gateway or WiFi lock.
        /// Can be called directly if lock is WiFi or connected to gateway.
        /// </summary>
        Cloud = 2
    }

    public enum LoginOtpDeliveryMethod
    {
        Email,
        Phone
    }
    public enum RowStatus
    {
        Deleted,
        Active,
        DeletedByAdmin
    }
    public enum OtpActionType
    {
        Login_Sms,
        Login_Email,

        Password_Reset_Phone,
        Password_Reset_Email,

        Update_Phone,
        Update_Email,
    }
}
