import { checkProjectExistsAPI } from "../../api/CreateProjectPage/checkProjectExists";
import { createProjectAPI } from "../../api/CreateProjectPage/createProject";

export default function useCreateProject() {
  const createProject = async (data) => {
    return createProjectAPI(data); // data = { title, token, ... }
  };

  const checkProjectExists = async (projectName) => {
    return checkProjectExistsAPI(projectName); 
  };

  return { createProject, checkProjectExists };
}