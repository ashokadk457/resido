namespace Resido.Model.TTLockDTO.ResponseDTO.EkeysRsp
{
    public class ChangeKeyPeriodResponseDTO : ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
