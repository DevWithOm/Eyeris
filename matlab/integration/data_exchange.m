function payload = data_exchange(caseId, result)
arguments
    caseId (1,1) string
    result (1,1) struct
end
payload = struct("case_id", caseId, "result", result);
end
