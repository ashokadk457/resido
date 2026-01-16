using Resido.Model.TTLockDTO.ResponseDTO.LockRsp;

namespace Resido.Model.TTLockDTO.ResponseDTO.EkeysRsp
{
    public class ListKeysResponseDTO : ITTLockErrorResponse
    {
        public List<TTLockKeyDTO> List { get; set; }
        public int PageNo { get; set; }
        public int PageSize { get; set; }
        public int Pages { get; set; }
        public int Total { get; set; }

        // TTLock error response fields
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }

    public class TTLockKeyDTO:SmartLockUsageCountDTO
    {
        public int KeyId { get; set; }
        public string LockData { get; set; }
        public int LockId { get; set; }
        public string UserType { get; set; }
        public string KeyStatus { get; set; }
        public string LockName { get; set; }
        public string LockAlias { get; set; }
        public string LockMac { get; set; }
        public string NoKeyPwd { get; set; }
        public int ElectricQuantity { get; set; }
        public long StartDate { get; set; }
        public long EndDate { get; set; }
        public string Remarks { get; set; }
        public int KeyRight { get; set; }//keyRight	Int	Is ekey authorized: 0-NO, 1-yes
        public string FeatureValue { get; set; }
        public int RemoteEnable { get; set; }
        public int PassageMode { get; set; }
        public long TimezoneRawOffset { get; set; }
        public int GroupId { get; set; }
        public string GroupName { get; set; }
        public int HasGateway { get; set; }
     
    }

}
