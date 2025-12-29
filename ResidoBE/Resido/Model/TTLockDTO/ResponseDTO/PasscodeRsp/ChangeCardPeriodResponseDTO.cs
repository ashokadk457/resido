namespace Resido.Model.TTLockDTO.ResponseDTO.PasscodeRsp
{
    /// <summary>
    /// TTLock API response for change card period.
    /// </summary>
    public class ChangeCardPeriodResponseDTO : ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
