//src/hooks/CreateProjectPage/useCreateProject.js
import { createProjectAPI } from "../../api/CreateProjectPage/api.js";

export default function useCreateProject() {
  const createProject = async (data) => {
    return createProjectAPI(data); // data = { title, token, ... }
  };


return { createProject };

}